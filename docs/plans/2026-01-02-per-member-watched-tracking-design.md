# Per-Member Watched Tracking

## Problem

Currently, when a movie is marked as "watched," it disappears from the pool for everyone. This prevents scenarios like:
- Tim and Monty watch a movie together, but Sally, John, and Mary should still be able to pick it for their movie night
- Tim saw a movie years ago and would happily rewatch it with family

## Solution

Track watched status per-member, allowing movies to remain available for family members who haven't seen them.

---

## Data Model

### New Table: `member_watched`

```sql
CREATE TABLE member_watched (
    id INTEGER PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES members(id),
    movie_id INTEGER NOT NULL REFERENCES movies(id),
    watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    would_rewatch BOOLEAN DEFAULT FALSE,
    UNIQUE(member_id, movie_id)
);
```

### Relationship to Existing Tables

```
members ──┬── swipes ─────────── movies
          │                        │
          ├── member_watched ──────┤
          │                        │
          └── watchlist_entries ───┘
```

- `swipes`: Unchanged - tracks yes/no votes
- `watchlist_entries.is_active`: Now only means "in the pool" (not "unwatched")
- `member_watched`: New per-member watched status with rewatch preference

---

## State Logic

### When Swiping

| Watched Toggle | Swipe | Records Created |
|----------------|-------|-----------------|
| OFF | No | `swipes(direction: no)` |
| OFF | Yes | `swipes(direction: yes)` |
| ON | No | `swipes(direction: no)` + `member_watched(would_rewatch: false)` |
| ON | Yes | `swipes(direction: yes)` + `member_watched(would_rewatch: true)` |

### Movie Night Matching

A movie matches for selected participants when:
1. All participants swiped "yes", AND
2. All participants are "eligible" where eligible means:
   - No `member_watched` record exists, OR
   - `member_watched.would_rewatch = true`

### Movie Night Completion

When "Mark as Watched" is confirmed:
- Create `member_watched` record for each checked participant
- `would_rewatch` defaults to `false`

---

## UI Changes

### Swipe Screen

Add watched toggle (👁) on movie card:

```
┌───────────────────┐
│                   │
│   [Movie Poster]  │
│              👁 ←── Watched toggle (top-right)
│                   │
└───────────────────┘
```

- Tap to toggle watched state
- Visual: outlined = not watched, filled = watched
- Yes/No buttons unchanged - still dismiss the card

### Watchlist Tab

Add "Show Watched" toggle in header:

```
┌─────────────────────────────┐
│  Watchlist    [Show Watched ○]
├─────────────────────────────┤
│  (List of unwatched movies) │
└─────────────────────────────┘
```

When toggled ON, shows personal watched list:

```
┌─────────────────────────────┐
│  Watched      [Show Watched ●]
├─────────────────────────────┤
│  Dune                  [♡]  │ ← Tap to toggle would_rewatch
│  Watched Jan 1              │
│                             │
│  The Godfather         [♥]  │ ← Filled = would rewatch
│  Watched Dec 15             │
└─────────────────────────────┘
```

### Movie Night Completion

New screen after winner is shown:

```
┌─────────────────────────────┐
│      🎉 Movie Night! 🎉     │
│                             │
│    [Winner Poster]          │
│                             │
│   Did you watch it?         │
│                             │
│   ☑ Tim                     │
│   ☑ Monty                   │
│   ☐ Sally                   │
│                             │
│   [Mark as Watched]         │
│                             │
│   Skip                      │
└─────────────────────────────┘
```

- Participants pre-checked
- Can adjust who actually watched
- Skip returns home without marking

---

## API Changes

### New Endpoints

```
POST   /api/watched/                    # Mark movie as watched for members
GET    /api/watched/{member_id}         # Get member's watched list
PATCH  /api/watched/{member_id}/{movie_id}  # Update would_rewatch
```

### Modified Endpoints

```
GET    /api/swipes/queue/{member_id}    # No changes needed
POST   /api/swipes/                     # Accept optional watched flag
POST   /api/movie-night/matches         # Filter by watched status
GET    /api/watchlist/                  # Accept show_watched filter
```

---

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Everyone watched a movie | Never matches, stays in watched lists, anyone can toggle ♥ to revive |
| New family member joins | No watched records, sees all movies in swipe queue |
| Change mind after watching | Toggle ♥ off in watched list, excluded from future matches |
| Existing movies (migration) | No `member_watched` records = treated as unwatched by everyone |

---

## Out of Scope

- Auto-removal of movies when everyone has watched
- "Who's watched this" badges on movie cards
- Notifications
- Changes to History tab

---

## Implementation Order

1. Database migration (new `member_watched` table)
2. Backend API updates (watched endpoints, matching logic)
3. Swipe screen UI (watched toggle)
4. Movie Night completion flow
5. Watchlist toggle and watched list view
