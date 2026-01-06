# "Just Us" Filter - Design Document

## Overview

Add visibility into which absent family members have also voted YES on movies during Movie Night selection, plus a filter to show only "exclusive" matches that no absent members want.

## Problem

When a subset of family members (e.g., Tim, Monty, Beck) have movie night, the current picker shows all movies any of them voted YES on. Sometimes they'd prefer to save "crowd pleasers" (movies everyone wants) for when the whole family is present, and instead watch something only they want.

## Solution

Two changes:

1. **Show absent YES voters** on movie cards with reduced opacity avatars
2. **"Just Us" filter** to show only movies where no absent member voted YES

---

## Backend Changes

### Endpoint: `POST /api/movie-night/matches`

**New response field per match:**

```python
absent_yes_voters: list[MemberResponse]  # Members NOT present who voted YES
```

**Implementation:**

1. Query all members not in `present_member_ids`
2. For each watchlist movie, look up YES swipes from absent members
3. Include those voters in the response

**Schema update (`MatchedMovie`):**

```python
class MatchedMovie(BaseModel):
    movie: MovieResponse
    yes_votes: int
    total_present: int
    is_full_match: bool
    voters: list[MemberResponse]           # Present members who voted YES
    absent_yes_voters: list[MemberResponse] # NEW: Absent members who voted YES
```

---

## Frontend Changes

### Card Display (Voter Row)

**Current:**
```
[✓] [avatar][avatar][avatar]  "2/3 yes"
```

**New:**
```
[✓] [avatar][avatar][avatar][grayed][grayed]  "2/3 yes"
```

- All YES voters in one continuous avatar stack
- Present voters: full opacity
- Absent voters: 40-50% opacity
- Same avatar size throughout
- No dividers or labels
- Vote count remains present-context only ("X/Y yes")

### Filter Chip

Add to existing quick filters:
```
[< 2hrs] [🍅 70%+] [no 18+] [New] [Just Us]
```

**Behavior:**
- When active: `filteredMatches.filter(m => m.absent_yes_voters.length === 0)`
- Empty state: Standard "No movies match these filters" with "Clear Filters" button
- Always visible (even when all members present)

---

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Solo movie night | "Just Us" shows movies only that person voted YES on |
| Everyone present | "Just Us" has no effect (absent_yes_voters always empty) |
| No exclusive matches | Standard empty filter state, user can toggle off and scan visually |

---

## Files to Modify

**Backend:**
- `app/routers/movie_night.py` - Add absent voter query logic
- `app/schemas.py` - Add `absent_yes_voters` to `MatchedMovie`

**Frontend:**
- `src/pages/MovieNight.tsx` - Update voter row rendering, add filter chip
- `src/pages/MovieNight.css` - Add `.voter-avatar.absent` opacity style
- `src/types/index.ts` - Add `absent_yes_voters` to `MatchedMovie` type
