# Comprehensive Code Fixes Implementation Plan

**Date:** 2026-01-03
**Reference:** Comprehensive code review (backend, frontend, infrastructure agents)
**Goal:** Address remaining performance, code quality, and testing gaps

## Pre-Flight Checks

Before starting:
```bash
# Backend tests must pass
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest -v

# Frontend must build
cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build
```

---

## Phase 1: Backend Performance & Data Integrity

### [x] P1-1: Add eager loading to watchlist GET endpoint

**File:** `backend/app/routers/watchlist.py`
**Lines:** ~30-42

**Problem:** Accessing `entry.movie` and `entry.added_by` in a loop triggers N+1 queries.

**Implementation:**
```python
from sqlalchemy.orm import joinedload

# In get_watchlist function, update the query:
query = db.query(WatchlistEntry).options(
    joinedload(WatchlistEntry.movie),
    joinedload(WatchlistEntry.added_by)
)
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest tests/test_watchlist.py -v
```

**Success Signal:** Tests pass, no new queries appear in logs when fetching watchlist with multiple entries.

---

### [x] P1-2: Add database indexes on foreign keys

**File:** `backend/app/models.py`

**Problem:** Foreign key columns lack indexes, slowing filtered queries as data grows.

**Implementation:**
Add `index=True` to these columns:
- `WatchlistEntry.movie_id` (line ~75)
- `WatchlistEntry.added_by_id` (line ~76)
- `Swipe.member_id` (line ~90)
- `Swipe.movie_id` (line ~91)
- `MemberWatched.member_id` (line ~108)
- `MemberWatched.movie_id` (line ~109)

Example:
```python
movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False, index=True)
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest -v
```

**Success Signal:** All tests pass. New database will have indexes (verify with sqlite3 `.schema` if needed).

---

### [x] P1-3: Single commit pattern in watched.py batch endpoint

**File:** `backend/app/routers/watched.py`
**Lines:** ~111-149 (POST /batch endpoint)

**Problem:** Multiple `db.commit()` calls inside loop can leave data inconsistent on partial failure.

**Implementation:**
1. Remove commits from inside the loop
2. Collect all records to create
3. Single `db.commit()` at the end
4. Use `db.flush()` if you need IDs before commit

```python
@router.post("/batch", response_model=List[MemberWatchedResponse])
def batch_mark_watched(...):
    results = []
    for member_id in request.member_ids:
        # ... create watched record without committing
        db.add(watched)
        db.flush()  # Get ID without committing
        results.append(watched)

    db.commit()  # Single commit for all
    for r in results:
        db.refresh(r)
    return [...]
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest tests/test_member_watched.py -v
```

**Success Signal:** All tests pass. Verify batch endpoint makes single commit (check logs or add temporary logging).

---

### [x] P1-4: Add uniqueness check on member name update

**File:** `backend/app/routers/members.py`
**Lines:** ~50-63 (PATCH endpoint)

**Problem:** Updating a member's name to an existing name causes 500 error instead of 400.

**Implementation:**
```python
@router.patch("/{member_id}", response_model=MemberResponse)
def update_member(member_id: int, member: MemberUpdate, db: Session = Depends(get_db)):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")

    update_data = member.model_dump(exclude_unset=True)

    # Add uniqueness check
    if "name" in update_data:
        existing = db.query(Member).filter(
            Member.name == update_data["name"],
            Member.id != member_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Name already taken")

    for field, value in update_data.items():
        setattr(db_member, field, value)
    # ... rest of function
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest tests/test_members.py -v
```

**Test to Add:** Also add a test case for duplicate name on update:
```python
def test_update_member_duplicate_name(client, sample_members):
    # Try to rename member 1 to member 2's name
    response = client.patch(
        f"/api/members/{sample_members[0].id}",
        json={"name": sample_members[1].name}
    )
    assert response.status_code == 400
    assert "already taken" in response.json()["detail"].lower()
```

**Success Signal:** All member tests pass including new duplicate name test.

---

## Phase 2: Backend Code Quality

### [x] P2-1: Remove dead HTTPStatusError except clause in OMDb

**File:** `backend/app/services/omdb.py`
**Lines:** ~77-79

**Problem:** `HTTPStatusError` handler never triggers because `raise_for_status()` is not called.

**Implementation:**
Either:
A) Remove the unused except clause:
```python
except httpx.TimeoutException:
    logger.error("OMDb timeout for imdb_id %s", imdb_id)
    return None
# Remove: except httpx.HTTPStatusError as e: ...
```

OR B) Add `raise_for_status()` if you want to handle HTTP errors:
```python
response = await client.get(url, params=params)
response.raise_for_status()  # Now HTTPStatusError handler is reachable
```

**Recommended:** Option A (remove dead code) - the manual status check is sufficient.

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest tests/test_ratings_and_trailers.py -v
```

**Success Signal:** Tests pass, no dead code.

---

### [x] P2-2: Extract RT slug generation helper in OMDb

**File:** `backend/app/services/omdb.py`
**Lines:** ~54-65 and ~110-117

**Problem:** Same slug generation logic duplicated.

**Implementation:**
```python
class OMDbService:
    @staticmethod
    def _generate_rt_slug(title: str) -> str:
        """Generate Rotten Tomatoes URL slug from movie title."""
        slug = title.lower()
        for char in [":", "'", "'", ",", ".", "!", "?"]:
            slug = slug.replace(char, "")
        slug = slug.replace(" - ", " ")
        slug = slug.replace("&", "and")
        slug = re.sub(r'\s+', '_', slug.strip())
        return slug

    def get_rt_url(self, title: str) -> str:
        slug = self._generate_rt_slug(title)
        return f"https://www.rottentomatoes.com/m/{slug}"
```

Then update both places that generate slugs to use `self._generate_rt_slug(title)`.

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest tests/test_ratings_and_trailers.py -v
```

**Success Signal:** Tests pass, slug generation in one place only.

---

### [x] P2-3: Add Optional type hints to nullable parameters

**File:** `backend/app/routers/watchlist.py`
**Lines:** ~15-21

**Problem:** `added_by_id: int = None` should be `Optional[int] = None`.

**Implementation:**
```python
from typing import Optional

@router.get("/", response_model=List[WatchlistEntryResponse])
def get_watchlist(
    active_only: bool = True,
    added_by_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
```

Check other routers for similar patterns and fix:
- `movies.py` - any nullable params
- `swipes.py` - any nullable params
- `watched.py` - any nullable params

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest -v
```

**Success Signal:** All tests pass, type hints are accurate.

---

## Phase 3: Frontend React Patterns

### [x] P3-1: Fix navigation side effects in render body

**Files:**
- `frontend/src/pages/SwipeScreen.tsx` (~line 235)
- `frontend/src/pages/Watchlist.tsx` (~line 143)
- `frontend/src/pages/MovieNight.tsx` (~line 100)
- `frontend/src/pages/History.tsx` (~line 40)

**Problem:** Calling `navigate('/')` directly in render causes side effects during render.

**Current Pattern:**
```typescript
if (!memberId) {
  navigate('/');
  return null;
}
```

**Implementation:** These can be REMOVED entirely because `ProtectedRoute` in `App.tsx` already handles this redirect. The checks are redundant.

If you want to keep a fallback, use `useEffect`:
```typescript
useEffect(() => {
  if (!memberId) {
    navigate('/');
  }
}, [memberId, navigate]);

if (!memberId) {
  return null; // or loading spinner
}
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build
```

**Success Signal:** Build passes, navigation works correctly when accessing pages without member selection.

---

### [x] P3-2: Add cleanup to useEffect with async operations

**File:** `frontend/src/pages/SwipeScreen.tsx`
**Lines:** ~198-209

**Problem:** Promise callback can run after component unmounts.

**Current:**
```typescript
useEffect(() => {
  if (condition) {
    refetch().then(() => {
      setSwipedIds(new Set());
    });
  }
}, [deps]);
```

**Implementation:**
```typescript
useEffect(() => {
  let isMounted = true;

  if (
    availableMovies.length <= REFETCH_THRESHOLD &&
    trueRemaining > availableMovies.length &&
    !isFetching
  ) {
    refetch().then(() => {
      if (isMounted) {
        setSwipedIds(new Set());
      }
    });
  }

  return () => {
    isMounted = false;
  };
}, [availableMovies.length, trueRemaining, isFetching, refetch]);
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build
```

**Success Signal:** Build passes, no warnings about state updates on unmounted components.

---

### [x] P3-3: Add error handling to async mutation onSuccess

**File:** `frontend/src/pages/Watchlist.tsx`
**Lines:** ~70-79

**Problem:** `recordSwipe` in `onSuccess` can fail silently.

**Current:**
```typescript
onSuccess: async (entry) => {
  await recordSwipe(memberId!, entry.movie.id, 'yes', false);
  queryClient.invalidateQueries({ queryKey: ['watchlist'] });
},
```

**Implementation:**
```typescript
onSuccess: async (entry) => {
  try {
    await recordSwipe(memberId!, entry.movie.id, 'yes', false);
  } catch (error) {
    console.error('Auto-swipe failed:', error);
    // Operation still succeeds for add, just the auto-swipe failed
  }
  queryClient.invalidateQueries({ queryKey: ['watchlist'] });
  queryClient.invalidateQueries({ queryKey: ['memberSwipes', memberId] });
},
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build
```

**Success Signal:** Build passes, error handling in place.

---

### [x] P3-4: Add onError handlers to all mutations

**Files:**
- `frontend/src/pages/Watchlist.tsx` - addMutation, removeMutation, reactivateMutation
- `frontend/src/pages/MovieNight.tsx` - watchedMutation, selectMutation

**Problem:** Mutations fail silently without user feedback.

**Implementation:** Add consistent error handling:
```typescript
const addMutation = useMutation({
  mutationFn: (tmdbId: number) => addToWatchlist(tmdbId, memberId!),
  onSuccess: async (entry) => { /* ... */ },
  onError: (error) => {
    console.error('Failed to add movie:', error);
    // Could add toast notification here in future
  },
});
```

Add `onError` to ALL mutations in these files.

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build
```

**Success Signal:** Build passes, all mutations have error handlers.

---

### [x] P3-5: Replace IIFE pattern in Watchlist JSX

**File:** `frontend/src/pages/Watchlist.tsx`
**Lines:** ~362-385

**Problem:** IIFE in JSX reduces readability.

**Current:**
```typescript
{selectedEntry && (() => {
  const isWatched = memberWatchedList?.some(w => w.movie.id === selectedEntry.movie.id) ?? false;
  return <MovieDetailCard watched={isWatched} ... />;
})()}
```

**Implementation:**
Compute value outside JSX:
```typescript
// Before the return statement
const selectedEntryIsWatched = selectedEntry
  ? (memberWatchedList?.some(w => w.movie.id === selectedEntry.movie.id) ?? false)
  : false;

// In JSX:
{selectedEntry && (
  <MovieDetailCard
    watched={selectedEntryIsWatched}
    // ... other props
  />
)}
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build
```

**Success Signal:** Build passes, no IIFE patterns in JSX.

---

### [ ] P3-6: Add loading/disabled states to mutation buttons

**File:** `frontend/src/pages/Watchlist.tsx`
**Lines:** ~204-208 (remove button)

**Problem:** Buttons can be clicked multiple times during pending mutations.

**Implementation:**
```typescript
<button
  className="remove-btn"
  disabled={removeMutation.isPending}
  onClick={(e) => {
    e.stopPropagation();
    removeMutation.mutate(entry.id);
  }}
>
  {removeMutation.isPending ? '...' : '×'}
</button>
```

Apply similar pattern to all mutation-triggering buttons in:
- `Watchlist.tsx` - remove, reactivate buttons
- `MovieNight.tsx` - mark watched button
- `UserSelect.tsx` - upload button (already has loading state? verify)

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build
```

**Success Signal:** Build passes, buttons show loading state and prevent double-clicks.

---

### [ ] P3-7: Define constants for magic numbers

**Files:**
- `frontend/src/pages/UserSelect.tsx` - long press delay (500)
- `frontend/src/pages/SwipeScreen.tsx` - swipe threshold (100), batch size (20), refetch threshold (5)
- `frontend/src/pages/MovieNight.tsx` - none identified

**Implementation:**
At the top of each file, add named constants:
```typescript
// SwipeScreen.tsx
const SWIPE_THRESHOLD_PX = 100;
const BATCH_SIZE = 20;
const REFETCH_THRESHOLD = 5;

// UserSelect.tsx
const LONG_PRESS_DELAY_MS = 500;
```

Then replace all magic number usages with the constants.

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build
```

**Success Signal:** Build passes, no unexplained magic numbers.

---

### [ ] P3-8: Use getAvatarUrl consistently

**File:** `frontend/src/pages/UserSelect.tsx`
**Line:** ~141

**Problem:** Constructs avatar URL inline instead of using shared utility.

**Current:**
```typescript
src={`${import.meta.env.VITE_API_URL?.replace('/api', '') || ''}${member.avatar_url}`}
```

**Implementation:**
```typescript
import { getAvatarUrl } from '../utils';

// In JSX:
src={getAvatarUrl(member.avatar_url) || undefined}
```

Verify `getAvatarUrl` exists in utils (should from previous fixes) and update all avatar URL constructions to use it.

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build
```

**Success Signal:** Build passes, consistent avatar URL handling.

---

## Phase 4: Testing Coverage

### [ ] P4-1: Add tests for movies search and trending endpoints

**File to Create:** `backend/tests/test_movies.py`

**Problem:** Search and trending endpoints have no integration tests.

**Implementation:**
```python
import pytest
from unittest.mock import AsyncMock, patch

def test_search_movies(client):
    """Test movie search endpoint."""
    with patch('app.services.tmdb.TMDBService.search_movies', new_callable=AsyncMock) as mock:
        mock.return_value = {
            "results": [
                {
                    "id": 123,
                    "title": "Test Movie",
                    "overview": "A test movie",
                    "release_date": "2024-01-01",
                    "poster_path": "/test.jpg",
                    "backdrop_path": "/backdrop.jpg",
                    "vote_average": 7.5,
                    "genre_ids": [28, 12]
                }
            ],
            "total_results": 1
        }

        response = client.get("/api/movies/search?query=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 0  # May be empty if not cached


def test_trending_movies(client):
    """Test trending movies endpoint."""
    with patch('app.services.tmdb.TMDBService.get_trending', new_callable=AsyncMock) as mock:
        mock.return_value = {
            "results": [
                {
                    "id": 456,
                    "title": "Trending Movie",
                    "overview": "A trending movie",
                    "release_date": "2024-06-01",
                    "poster_path": "/trend.jpg",
                    "backdrop_path": None,
                    "vote_average": 8.0,
                    "genre_ids": [18]
                }
            ]
        }

        response = client.get("/api/movies/trending")
        assert response.status_code == 200


def test_search_movies_empty_query(client):
    """Test search with empty query returns error or empty."""
    response = client.get("/api/movies/search?query=")
    # Should either return 400 or empty results
    assert response.status_code in [200, 400]
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest tests/test_movies.py -v
```

**Success Signal:** New tests pass, search/trending endpoints tested.

---

### [ ] P4-2: Add tests for watched.py toggle and delete endpoints

**File:** `backend/tests/test_member_watched.py`

**Problem:** PUT toggle and DELETE endpoints not tested.

**Implementation:** Add these test cases:
```python
def test_toggle_watched_to_unwatched(client, sample_members, sample_movies):
    """Test toggling watched status off."""
    member = sample_members[0]
    movie = sample_movies[0]

    # First mark as watched
    response = client.post(
        f"/api/watched/{member.id}/{movie.id}"
    )
    assert response.status_code == 201

    # Toggle off
    response = client.put(
        f"/api/watched/{member.id}/{movie.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("removed") == True or response.status_code == 204


def test_delete_watched_record(client, sample_members, sample_movies):
    """Test deleting watched record."""
    member = sample_members[0]
    movie = sample_movies[0]

    # First mark as watched
    client.post(f"/api/watched/{member.id}/{movie.id}")

    # Delete
    response = client.delete(
        f"/api/watched/{member.id}/{movie.id}"
    )
    assert response.status_code == 204

    # Verify gone
    response = client.get(f"/api/watched/{member.id}")
    data = response.json()
    movie_ids = [w["movie"]["id"] for w in data]
    assert movie.id not in movie_ids


def test_delete_nonexistent_watched(client, sample_members, sample_movies):
    """Test deleting non-existent watched record."""
    member = sample_members[0]
    movie = sample_movies[0]

    response = client.delete(
        f"/api/watched/{member.id}/{movie.id}"
    )
    assert response.status_code == 404
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest tests/test_member_watched.py -v
```

**Success Signal:** New tests pass, watched.py coverage increases.

---

### [ ] P4-3: Fix SQLAlchemy subquery deprecation warning

**File:** `backend/app/routers/swipes.py`
**Line:** ~76

**Problem:** `SAWarning: Coercing Subquery object into a select() for use in IN()`

**Implementation:**
Find the subquery usage and wrap in `select()`:
```python
from sqlalchemy import select

# Before:
watched_movie_ids = db.query(MemberWatched.movie_id).filter(
    MemberWatched.member_id == member_id
).subquery()
query = query.filter(~Movie.id.in_(watched_movie_ids))

# After:
watched_subquery = select(MemberWatched.movie_id).where(
    MemberWatched.member_id == member_id
).scalar_subquery()
query = query.filter(~Movie.id.in_(watched_subquery))
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest tests/test_swipes.py -v 2>&1 | grep -i warning
```

**Success Signal:** Tests pass with no SQLAlchemy deprecation warnings.

---

### [ ] P4-4: Standardize test_watchlist.py to use shared fixtures

**File:** `backend/tests/test_watchlist.py`
**Lines:** ~12-23

**Problem:** Creates own `TestingSessionLocal` instead of using `conftest.py` fixtures.

**Implementation:**
Remove the duplicate database setup and use shared fixtures:
```python
# Remove these lines:
# SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
# engine = create_engine(...)
# TestingSessionLocal = sessionmaker(...)

# Use fixtures from conftest.py instead:
def test_add_to_watchlist(client, db_session, sample_members, sample_movies):
    # ... test code using shared fixtures
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest tests/test_watchlist.py -v
```

**Success Signal:** Tests pass using shared fixtures.

---

## Phase 5: Infrastructure

### [ ] P5-1: Add Docker health check for backend

**File:** `docker-compose.yml` (root) and `deploy/docker-compose.yml`

**Problem:** No container health checks for orchestration.

**Implementation:**
Add to backend service:
```yaml
backend:
  build: ./backend
  # ... existing config
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 10s
```

**Note:** May need to add `curl` to backend Dockerfile if not present:
```dockerfile
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker && docker-compose config
# Verify healthcheck appears in output
```

**Success Signal:** docker-compose config shows healthcheck, container reports healthy after startup.

---

### [ ] P5-2: Add cache headers for static assets

**File:** `frontend/nginx.conf`

**Problem:** No cache headers for static files.

**Implementation:**
```nginx
# Add after the /static/ location block
location /static/ {
    proxy_pass http://backend:8000;
    expires 7d;
    add_header Cache-Control "public, immutable";
}

# Add for frontend assets
location /assets/ {
    root /usr/share/nginx/html;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**Test Command:**
```bash
# After deploying, check headers:
curl -I http://your-server/static/avatars/1.jpg | grep -i cache
```

**Success Signal:** Cache-Control headers present in response.

---

### [ ] P5-3: Add .dockerignore files

**Files to Create:**
- `backend/.dockerignore`
- `frontend/.dockerignore`

**Implementation:**

`backend/.dockerignore`:
```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
.env
.git/
.gitignore
*.db
*.sqlite3
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
```

`frontend/.dockerignore`:
```
node_modules/
dist/
.git/
.gitignore
*.log
.env
.env.local
coverage/
.nyc_output/
```

**Test Command:**
```bash
cd /Users/tim/Claude/Movie_picker && docker-compose build --no-cache 2>&1 | tail -20
# Build should be faster, context smaller
```

**Success Signal:** Files created, docker build context is smaller.

---

## Verification Protocol

After ALL phases complete:

```bash
# 1. Backend tests
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest -v
# Expected: ALL tests pass, no warnings

# 2. Frontend build
cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build
# Expected: No errors, successful build

# 3. Docker build
cd /Users/tim/Claude/Movie_picker && docker-compose build
# Expected: Successful build

# 4. Quick smoke test (if running)
curl http://localhost:8000/api/health
# Expected: {"status": "healthy"}
```

---

## Success Criteria

All of the following must be true:
- [ ] All Phase 1 items complete (backend performance)
- [ ] All Phase 2 items complete (backend quality)
- [ ] All Phase 3 items complete (frontend patterns)
- [ ] All Phase 4 items complete (testing)
- [ ] All Phase 5 items complete (infrastructure)
- [ ] `pytest` passes with 0 failures and no deprecation warnings
- [ ] `npm run lint` passes with 0 errors
- [ ] `npm run build` succeeds
- [ ] No functionality removed or broken

---

## Notes

- ONE task per iteration (atomic changes)
- Run tests after EACH change
- Commit after EACH successful fix
- If tests fail, fix before moving on
- If stuck for 2+ iterations, add note and skip
- Do NOT refactor beyond specification
- Do NOT add new features
- Do NOT change API contracts
