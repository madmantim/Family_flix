# Discover Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Discover" button to Watchlist that shows Popular and Highly Rated movies available for home viewing, with tap-to-add functionality.

**Architecture:** New TMDB discover endpoint with preset tab configurations. Frontend modal with tabs, client-side filtering of already-added movies, instant tap-to-add with animations.

**Tech Stack:** FastAPI, TMDB API, React, TanStack Query, Framer Motion

---

## Task 1: Add TMDB Discover Service Method

**Files:**
- Modify: `backend/app/services/tmdb.py:74-84`
- Test: `backend/tests/test_discover.py` (create)

**Step 1: Write the failing test**

Create `backend/tests/test_discover.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.tmdb import TMDBService


@pytest.mark.asyncio
async def test_discover_movies_popular():
    """Test discover_movies with popular sort"""
    mock_response = {
        "results": [{"id": 123, "title": "Test Movie", "release_date": "2025-12-01"}],
        "page": 1,
        "total_pages": 10,
        "total_results": 200
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = lambda: None

        service = TMDBService()
        result = await service.discover_movies(
            sort_by="popularity.desc",
            release_date_gte="2025-10-01",
            release_date_lte="2025-12-31",
            with_release_type="4|5"
        )

        assert result == mock_response
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "discover/movie" in str(call_args)


@pytest.mark.asyncio
async def test_discover_movies_highly_rated():
    """Test discover_movies with vote_average sort and vote_count filter"""
    mock_response = {
        "results": [{"id": 456, "title": "Rated Movie", "release_date": "2025-11-15"}],
        "page": 1,
        "total_pages": 5,
        "total_results": 100
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = lambda: None

        service = TMDBService()
        result = await service.discover_movies(
            sort_by="vote_average.desc",
            release_date_gte="2025-10-01",
            release_date_lte="2025-12-31",
            vote_count_gte=50,
            with_release_type="4|5"
        )

        assert result == mock_response
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_discover.py -v`
Expected: FAIL with "AttributeError: 'TMDBService' object has no attribute 'discover_movies'"

**Step 3: Write minimal implementation**

Add to `backend/app/services/tmdb.py` after the `get_popular` method (around line 84):

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
    """Discover movies with flexible filters for home availability"""
    params = {
        "page": page,
        "sort_by": sort_by,
        "with_release_type": with_release_type,
        "include_adult": False,
    }
    if release_date_gte:
        params["primary_release_date.gte"] = release_date_gte
    if release_date_lte:
        params["primary_release_date.lte"] = release_date_lte
    if vote_count_gte:
        params["vote_count.gte"] = vote_count_gte

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TMDB_BASE_URL}/discover/movie",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_discover.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add backend/app/services/tmdb.py backend/tests/test_discover.py
git commit -m "feat(backend): add discover_movies method to TMDB service"
```

---

## Task 2: Add Discover API Endpoint

**Files:**
- Modify: `backend/app/routers/movies.py`
- Modify: `backend/tests/test_discover.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_discover.py`:

```python
from datetime import datetime, timedelta


def test_discover_endpoint_popular(client, mocker):
    """Test GET /movies/discover?tab=popular"""
    mock_results = {
        "results": [
            {"id": 123, "title": "Popular Movie", "release_date": "2025-12-01",
             "overview": "A popular film", "poster_path": "/poster.jpg", "vote_average": 7.5}
        ],
        "page": 1,
        "total_pages": 10,
        "total_results": 200
    }

    mocker.patch(
        "app.routers.movies.get_tmdb_service"
    ).return_value.discover_movies = AsyncMock(return_value=mock_results)

    response = client.get("/api/movies/discover?tab=popular")

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Popular Movie"


def test_discover_endpoint_highly_rated(client, mocker):
    """Test GET /movies/discover?tab=highly-rated"""
    mock_results = {
        "results": [
            {"id": 456, "title": "Rated Movie", "release_date": "2025-11-15",
             "overview": "A highly rated film", "poster_path": "/rated.jpg", "vote_average": 8.5}
        ],
        "page": 1,
        "total_pages": 5,
        "total_results": 100
    }

    mocker.patch(
        "app.routers.movies.get_tmdb_service"
    ).return_value.discover_movies = AsyncMock(return_value=mock_results)

    response = client.get("/api/movies/discover?tab=highly-rated")

    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["title"] == "Rated Movie"


def test_discover_endpoint_invalid_tab(client):
    """Test GET /movies/discover with invalid tab returns 400"""
    response = client.get("/api/movies/discover?tab=invalid")
    assert response.status_code == 400
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_discover.py::test_discover_endpoint_popular -v`
Expected: FAIL with 404 (endpoint doesn't exist)

**Step 3: Write minimal implementation**

Add to `backend/app/routers/movies.py` before the `get_movie` route:

```python
from datetime import datetime, timedelta

@router.get("/discover", response_model=TMDBSearchResponse)
async def discover_movies(
    tab: str = Query(..., regex="^(popular|highly-rated)$"),
    page: int = Query(1, ge=1),
    tmdb: TMDBService = Depends(get_tmdb_service)
):
    """Discover movies available for home viewing (streaming/VOD/disc)"""
    # Calculate date range (last 90 days)
    today = datetime.now()
    ninety_days_ago = today - timedelta(days=90)

    release_date_gte = ninety_days_ago.strftime("%Y-%m-%d")
    release_date_lte = today.strftime("%Y-%m-%d")

    if tab == "popular":
        results = await tmdb.discover_movies(
            sort_by="popularity.desc",
            release_date_gte=release_date_gte,
            release_date_lte=release_date_lte,
            with_release_type="4|5",
            page=page
        )
    else:  # highly-rated
        results = await tmdb.discover_movies(
            sort_by="vote_average.desc",
            release_date_gte=release_date_gte,
            release_date_lte=release_date_lte,
            vote_count_gte=50,
            with_release_type="4|5",
            page=page
        )

    return TMDBSearchResponse(
        results=[
            TMDBSearchResult(
                tmdb_id=m["id"],
                title=m["title"],
                year=int(m["release_date"][:4]) if m.get("release_date") else None,
                overview=m.get("overview"),
                poster_url=tmdb.get_poster_url(m.get("poster_path")),
                vote_average=m.get("vote_average")
            )
            for m in results.get("results", [])
        ],
        page=results.get("page", 1),
        total_pages=results.get("total_pages", 0),
        total_results=results.get("total_results", 0)
    )
```

Also add HTTPException import and handle invalid tab:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
```

Update the Query to provide better error:
```python
tab: str = Query(..., description="Tab: 'popular' or 'highly-rated'"),
```

Add validation at start of function:
```python
if tab not in ("popular", "highly-rated"):
    raise HTTPException(status_code=400, detail="Invalid tab. Use 'popular' or 'highly-rated'")
```

**Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_discover.py -v`
Expected: PASS (all tests)

**Step 5: Run full backend test suite**

Run: `cd backend && python -m pytest`
Expected: All tests pass

**Step 6: Commit**

```bash
git add backend/app/routers/movies.py backend/tests/test_discover.py
git commit -m "feat(backend): add /movies/discover endpoint with popular and highly-rated tabs"
```

---

## Task 3: Add Frontend API Function

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/types/index.ts` (if needed)

**Step 1: Add discoverMovies function to client.ts**

Add after the `getTrending` function in `frontend/src/api/client.ts`:

```typescript
export const discoverMovies = (tab: 'popular' | 'highly-rated', page = 1) =>
  api.get<TMDBSearchResponse>('/movies/discover', { params: { tab, page } }).then(r => r.data);
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "feat(frontend): add discoverMovies API function"
```

---

## Task 4: Add Discover Button to Watchlist Header

**Files:**
- Modify: `frontend/src/pages/Watchlist.tsx`
- Modify: `frontend/src/pages/Watchlist.css`

**Step 1: Add state for discover modal**

In `Watchlist.tsx`, add new state after existing state declarations:

```typescript
const [showDiscover, setShowDiscover] = useState(false);
const [discoverTab, setDiscoverTab] = useState<'popular' | 'highly-rated'>('popular');
```

**Step 2: Add Discover button to header**

Update the header-controls div to add the Discover button:

```tsx
<div className="header-controls">
  <label className="show-watched-toggle">
    <span>Show Watched</span>
    <input
      type="checkbox"
      checked={showWatched}
      onChange={(e) => setShowWatched(e.target.checked)}
    />
  </label>
  {!showWatched && (
    <>
      <button className="discover-btn" onClick={() => setShowDiscover(true)}>
        Discover
      </button>
      <button className="add-btn" onClick={() => setShowSearch(true)}>
        + Add
      </button>
    </>
  )}
</div>
```

**Step 3: Add Discover button styling**

Add to `frontend/src/pages/Watchlist.css`:

```css
.discover-btn {
  background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
}

.discover-btn:hover {
  opacity: 0.9;
}
```

**Step 4: Verify it renders**

Run: `cd frontend && npm run dev`
Open browser, navigate to Watchlist, verify "Discover" button appears

**Step 5: Commit**

```bash
git add frontend/src/pages/Watchlist.tsx frontend/src/pages/Watchlist.css
git commit -m "feat(frontend): add Discover button to Watchlist header"
```

---

## Task 5: Add Discover Modal with Tabs

**Files:**
- Modify: `frontend/src/pages/Watchlist.tsx`
- Modify: `frontend/src/pages/Watchlist.css`

**Step 1: Add import for discoverMovies**

At the top of `Watchlist.tsx`, update imports:

```typescript
import {
  getWatchlist,
  searchMovies,
  addToWatchlist,
  removeFromWatchlist,
  getMemberWatched,
  updateWouldRewatch,
  recordSwipe,
  toggleWatched,
  removeWatched,
  getMemberSwipes,
  discoverMovies,
} from '../api/client';
```

**Step 2: Add discover query**

After the existing queries, add:

```typescript
const { data: discoverResults, isLoading: isDiscoverLoading } = useQuery({
  queryKey: ['discover', discoverTab],
  queryFn: () => discoverMovies(discoverTab),
  enabled: showDiscover,
});
```

**Step 3: Add the Discover Modal JSX**

After the search modal `AnimatePresence` block, add:

```tsx
<AnimatePresence>
  {showDiscover && (
    <motion.div
      className="discover-modal"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={() => setShowDiscover(false)}
    >
      <motion.div
        className="discover-content"
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        exit={{ y: 100 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="discover-header">
          <h2>Discover</h2>
          <button className="close-btn" onClick={() => setShowDiscover(false)}>
            ✕
          </button>
        </div>

        <div className="discover-tabs">
          <button
            className={`tab ${discoverTab === 'popular' ? 'active' : ''}`}
            onClick={() => setDiscoverTab('popular')}
          >
            Popular
          </button>
          <button
            className={`tab ${discoverTab === 'highly-rated' ? 'active' : ''}`}
            onClick={() => setDiscoverTab('highly-rated')}
          >
            Highly Rated
          </button>
        </div>

        <div className="discover-results">
          {isDiscoverLoading ? (
            <div className="loading">Loading...</div>
          ) : (
            <div className="discover-grid">
              {discoverResults?.results
                .filter(movie => !watchlist?.some(w => w.movie.tmdb_id === movie.tmdb_id))
                .map((movie) => (
                  <motion.div
                    key={movie.tmdb_id}
                    className="discover-item"
                    initial={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    layout
                    onClick={() => addMutation.mutate(movie.tmdb_id)}
                  >
                    <div
                      className="poster"
                      style={{
                        backgroundImage: movie.poster_url
                          ? `url(${movie.poster_url})`
                          : undefined,
                      }}
                    >
                      {!movie.poster_url && <span>No Poster</span>}
                      <div className="add-overlay">+</div>
                    </div>
                    <div className="title">{movie.title}</div>
                    {movie.vote_average && (
                      <div className="rating">★ {movie.vote_average.toFixed(1)}</div>
                    )}
                  </motion.div>
                ))}
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  )}
</AnimatePresence>
```

**Step 4: Add Discover Modal CSS**

Add to `frontend/src/pages/Watchlist.css`:

```css
.discover-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.discover-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #1a1a2e;
  overflow: hidden;
}

.discover-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.discover-header h2 {
  margin: 0;
  color: #fff;
  font-size: 1.5rem;
}

.discover-header .close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
}

.discover-tabs {
  display: flex;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.discover-tabs .tab {
  flex: 1;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 8px;
  color: #888;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.discover-tabs .tab.active {
  background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
  color: white;
}

.discover-results {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.discover-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 1rem;
}

.discover-item {
  cursor: pointer;
  transition: transform 0.2s;
}

.discover-item:hover {
  transform: scale(1.05);
}

.discover-item .poster {
  position: relative;
  aspect-ratio: 2/3;
  background: #2a2a3e;
  background-size: cover;
  background-position: center;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #555;
  font-size: 0.8rem;
  overflow: hidden;
}

.discover-item .add-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
}

.discover-item:hover .add-overlay {
  opacity: 1;
}

.discover-item .title {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #fff;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.discover-item .rating {
  font-size: 0.7rem;
  color: #f7931e;
  text-align: center;
}
```

**Step 5: Verify it works**

Run: `cd frontend && npm run dev`
Test:
1. Open Watchlist
2. Click "Discover"
3. Verify modal opens with tabs
4. Switch between Popular and Highly Rated
5. Click a movie to add it
6. Verify movie disappears from discover list

**Step 6: Commit**

```bash
git add frontend/src/pages/Watchlist.tsx frontend/src/pages/Watchlist.css
git commit -m "feat(frontend): add Discover modal with Popular and Highly Rated tabs"
```

---

## Task 6: Final Testing and Verification

**Step 1: Run all backend tests**

Run: `cd backend && python -m pytest -v`
Expected: All tests pass

**Step 2: Run frontend build**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors

**Step 3: Run frontend lint**

Run: `cd frontend && npm run lint`
Expected: No errors (warnings acceptable)

**Step 4: Manual E2E Testing**

Test the complete flow:
1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Navigate to Watchlist
4. Click "Discover"
5. Verify "Popular" tab shows movies
6. Switch to "Highly Rated" tab
7. Verify different movies appear
8. Add a movie by tapping
9. Verify movie disappears from Discover
10. Close modal
11. Verify movie appears in Watchlist

**Step 5: Final commit if any fixes needed**

If any fixes were made during testing:
```bash
git add -A
git commit -m "fix: address issues found during testing"
```

---

## Completion Checklist

- [ ] TMDB service has `discover_movies()` method
- [ ] `/movies/discover` endpoint works with `?tab=popular` and `?tab=highly-rated`
- [ ] Frontend has `discoverMovies()` API function
- [ ] "Discover" button appears in Watchlist header
- [ ] Discover modal opens with two tabs
- [ ] Popular tab shows recent popular movies available at home
- [ ] Highly Rated tab shows recent top-rated movies available at home
- [ ] Movies already in watchlist are filtered out
- [ ] Tapping a movie adds it and removes from discover list
- [ ] All backend tests pass
- [ ] Frontend builds without errors
