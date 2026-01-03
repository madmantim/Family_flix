# Voter Information on Movie Night Cards

## Summary

Add a voter avatar stack below the movie title on Movie Night browse cards, showing who voted YES for each movie. Full matches display a checkmark with "Everyone!" label.

## Motivation

When picking tonight's movie, users need to know who voted for it to make group decisions. Currently only vote counts are shown, not which family members voted.

## Design

### Data Model Changes

**Backend (`schemas.py`):**
```python
class MatchedMovie(BaseModel):
    movie: MovieResponse
    yes_votes: int
    total_present: int
    is_full_match: bool
    voters: List[MemberResponse]  # NEW: members who voted YES
```

**Backend (`movie_night.py`):**
- Collect the actual `Member` objects for each YES vote
- Already querying swipes, just need to return the member details

**Frontend (`types/index.ts`):**
```typescript
export interface MatchedMovie {
  movie: Movie;
  yes_votes: number;
  total_present: number;
  is_full_match: boolean;
  voters: Member[];  // NEW
}
```

### UI Component Design

**Avatar Stack Appearance:**
- Avatars overlap by ~40% (each 28-32px diameter)
- Stack displays left-to-right
- Positioned below the title/year, centered

**Full Match State:**
```
✓ [avatar][avatar][avatar][avatar]
        Everyone!
```
- Green checkmark prefix
- "Everyone!" label below in success color (#4ade80)

**Partial Match State:**
```
👍 [avatar][avatar][avatar] (3/4)
```
- Thumbs up prefix
- Count badge shows votes/present

**No interaction required** - visual display only.

### Visual Layout

```
┌─────────────────────────────┐
│        [Poster]             │
│                             │
│   Movie Title (2024)        │
│   ✓ [○][○][○][○]            │
│      Everyone!              │
│   🍅 92%  🍿 88%            │
│   Synopsis text...          │
│                             │
│   [▶ Watch Trailer]         │
│   [Watch This]              │
└─────────────────────────────┘
```

## Files to Modify

| File | Change |
|------|--------|
| `backend/app/schemas.py` | Add `voters: List[MemberResponse]` to `MatchedMovie` |
| `backend/app/routers/movie_night.py` | Populate `voters` from YES swipes |
| `frontend/src/types/index.ts` | Add `voters: Member[]` to `MatchedMovie` |
| `frontend/src/pages/MovieNight.tsx` | Add avatar stack below title in browse card |
| `frontend/src/pages/MovieNight.css` | Styles for `.voter-stack` |

No new files needed.
