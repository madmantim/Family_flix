# Watchlist Discover Feature Design

## Goal

Add a "Discover" feature to the Watchlist screen that surfaces quality recent movies available for home viewing, enabling quick bulk additions to the watchlist.

## User Problem

Currently, adding movies requires manual search. Users periodically review external sources (Rotten Tomatoes, streaming services) to find new releases, then search and add each one individually. This feature brings discovery into the app.

## User Experience

1. User opens Watchlist screen
2. Taps "Discover" button in header (next to existing "+ Add")
3. Full-screen modal opens with two tabs: **Popular** and **Highly Rated**
4. Both tabs show recent movies (last 90 days) available for home viewing (streaming/VOD/disc)
5. Movies already in watchlist are filtered out
6. Tapping a movie instantly adds it - movie fades out, grid reflows
7. User closes modal and returns to watchlist with new movies added

## Tab Definitions

### Popular
Movies people are currently watching/discussing.
- Digital/physical release only (`with_release_type=4|5`)
- Released in last 90 days
- Sorted by popularity (descending)

### Highly Rated
Best-reviewed recent releases.
- Digital/physical release only (`with_release_type=4|5`)
- Released in last 90 days
- Minimum 50 votes (filters obscure films)
- Sorted by vote average (descending)

## Backend Architecture

### TMDB Service (`backend/app/services/tmdb.py`)

New method wrapping TMDB's `/discover/movie` endpoint:

```python
async def discover_movies(
    self,
    sort_by: str = "popularity.desc",
    release_date_gte: str = None,
    release_date_lte: str = None,
    vote_count_gte: int = None,
    with_release_type: str = "4|5",
    page: int = 1
) -> dict:
```

### API Endpoint (`backend/app/routers/movies.py`)

```
GET /movies/discover?tab=popular&page=1
GET /movies/discover?tab=highly-rated&page=1
```

The `tab` parameter selects preset filter configurations. Returns `TMDBSearchResponse` format (same as existing endpoints).

## Frontend Architecture

### API Client (`frontend/src/api/client.ts`)

```typescript
export const discoverMovies = (tab: 'popular' | 'highly-rated', page = 1) =>
  api.get<TMDBSearchResponse>('/movies/discover', { params: { tab, page } }).then(r => r.data);
```

### Watchlist Component (`frontend/src/pages/Watchlist.tsx`)

New state:
- `showDiscover: boolean`
- `discoverTab: 'popular' | 'highly-rated'`

New UI elements:
- "Discover" button in header
- Discover modal with tab switcher
- Movie grid (reuses existing styling)
- Tap-to-add with fade animation

### Filtering Logic

Client-side filtering removes movies where `tmdb_id` exists in current watchlist. This keeps the API simple and avoids passing watchlist context to the backend.

## Files to Modify

| File | Changes |
|------|---------|
| `backend/app/services/tmdb.py` | Add `discover_movies()` method |
| `backend/app/routers/movies.py` | Add `GET /movies/discover` endpoint |
| `frontend/src/api/client.ts` | Add `discoverMovies()` function |
| `frontend/src/pages/Watchlist.tsx` | Add Discover button, modal, and logic |
| `frontend/src/pages/Watchlist.css` | Add tab styling (if needed) |

## Testing

### Backend Tests
- Test discover endpoint returns correct format
- Test `tab=popular` uses popularity sort
- Test `tab=highly-rated` uses vote_average sort and vote_count filter
- Test pagination works

### Manual Frontend Testing
- Verify both tabs load and display movies
- Verify already-added movies are filtered out
- Verify tap-to-add works and movie disappears
- Verify modal close returns to updated watchlist
