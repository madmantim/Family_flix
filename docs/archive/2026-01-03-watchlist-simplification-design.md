# Watchlist Simplification Design

## Problem Statement

The current Watchlist page has confusing filtering logic:
- A watched/unwatched toggle switches between two conceptually different views
- The `would_rewatch` flag creates an escape hatch that's hard to understand
- Watched state and "want to watch" state are conflated
- Movie Night marking watched removes movies from the pool (`is_active = False`), coupling two orthogonal concepts

## Design Goals

1. **Simplify mental model**: One signal for "want to watch" (the Y vote)
2. **Decouple concepts**: Watched state and pool membership are independent
3. **Remove redundant UI**: Eliminate confusing toggle
4. **Consistent ranking**: Watched status informs Movie Night ranking, doesn't block

## Core Logic

### Per-User States

| State | Signal | Storage |
|-------|--------|---------|
| Watched | Binary (watched/unwatched) | `MemberWatched` table |
| Want to watch | Y/N swipe vote | `Swipe` table |

### Watchlist View

**Shows:** Movies in the pool where the current user has voted **Y**.

```
Watchlist = WatchlistEntry.is_active == True
            AND Swipe.member_id == current_user
            AND Swipe.direction == YES
```

No filtering based on watched status. If you voted Y, it appears.

### State Transitions

| Action | Effect |
|--------|--------|
| Swipe Y on movie | Movie appears on your watchlist |
| Swipe N on movie | Movie removed from your watchlist |
| Mark watched (Movie Night) | Creates `MemberWatched` record, flips vote to N |
| Mark watched (individual toggle) | Creates `MemberWatched` record, vote unchanged |
| Remove from pool (trash) | Sets `WatchlistEntry.is_active = False` |

### Re-adding Watched Movies

If a user wants to rewatch a movie:
1. **From History page**: Add a "Want to watch again" action that flips vote to Y
2. **From Watchlist search/discover**: If movie is in pool, adding it again flips vote to Y

## Movie Night Algorithm

### Ranking

Sort by three keys:

1. **Y count** (descending) - more yes votes = better match
2. **N(W) count** (ascending) - fewer watched among N voters = fresher for group
3. **Recency** (newest first) - tiebreaker

Where:
- **Y** = voted Yes
- **N(U)** = voted No (or not voted) and Unwatched
- **N(W)** = voted No (or not voted) and has Watched

Example ordering for 4 present members:

| Rank | Pattern | Y count | N(W) count |
|------|---------|---------|------------|
| 1 | YYYY | 4 | 0 |
| 2 | YYYN(U) | 3 | 0 |
| 3 | YYYN(W) | 3 | 1 |
| 4 | YYN(U)N(U) | 2 | 0 |
| 5 | YYN(W)N(U) | 2 | 1 |
| 6 | YYN(W)N(W) | 2 | 2 |

### No Hard Blockers

Unlike current logic, watched status never excludes a movie. Movies where some members have watched and voted N still appear - just ranked lower.

## Schema Changes

### Remove `would_rewatch` Column

```sql
ALTER TABLE member_watched DROP COLUMN would_rewatch;
```

The Y vote now serves as the "would rewatch" signal.

### Update `MemberWatched` Model

```python
class MemberWatched(Base):
    __tablename__ = "member_watched"

    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    watched_at = Column(DateTime, default=datetime.utcnow)
    # REMOVED: would_rewatch = Column(Boolean, default=False)
```

### Decouple `is_active` from Watched

In `watched.py`, the `mark_watched` endpoint currently sets `WatchlistEntry.is_active = False`. Remove this side effect:

```python
# REMOVE these lines from mark_watched():
# watchlist_entries = db.query(WatchlistEntry).filter(...)
# for entry in watchlist_entries:
#     entry.is_active = False
```

## Backend Changes

### `POST /api/watched` (mark_watched)

Current behavior:
1. Create `MemberWatched` records
2. Set `would_rewatch` from request
3. Deactivate `WatchlistEntry`

New behavior:
1. Create `MemberWatched` records
2. Flip each member's swipe to N (if exists) or create N swipe
3. Do NOT touch `WatchlistEntry.is_active`

### `POST /api/movie-night/matches`

Update ranking algorithm:
1. Remove `would_rewatch` eligibility checks
2. Implement 3-tier ranking based on Y votes + watched status of N voters
3. Never exclude movies based on watched status

### `GET /api/watchlist`

No changes needed - frontend filtering changes.

### Remove/Update Endpoints

| Endpoint | Action |
|----------|--------|
| `PATCH /api/watched/{member_id}/{movie_id}` | Remove (was for `would_rewatch`) |
| `PUT /api/watched/{member_id}/{movie_id}` | Keep (toggle watched) |
| `DELETE /api/watched/{member_id}/{movie_id}` | Keep (unmark watched) |

## Frontend Changes

### Watchlist Page

1. **Remove** `showWatched` state and toggle button (👁/🙈)
2. **Update** filtering: show movies where user voted Y
3. **Remove** `would_rewatch` mutation and UI

### History Page

1. **Add** "Want to watch again" button on watched movies
2. Clicking creates/updates swipe to Y

### MovieDetailCard

1. **Remove** `would_rewatch` toggle
2. **Keep** watched toggle (👁 button)
3. Watched toggle only affects `MemberWatched`, not swipe

### Schemas/Types

Remove `would_rewatch` from:
- `MemberWatchedResponse`
- `MemberWatchedWithMovie`
- `MarkWatchedRequest`
- Frontend `MemberWatched` type

## Migration

No migration needed - still in building/testing phase with no valuable data.

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| "Want to watch" signal | Implicit (not watched OR would_rewatch) | Explicit (Y vote) |
| Watchlist shows | Unwatched + would_rewatch movies | Y-voted movies |
| Movie Night watched handling | Deactivates pool entry | Flips vote to N |
| `would_rewatch` flag | Exists | Removed |
| Watched/Unwatched toggle | Header toggle | Removed |
| Rewatch intent | Toggle would_rewatch | Change vote to Y |
