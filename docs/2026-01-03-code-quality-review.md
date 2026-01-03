# Code Quality Review

**Date:** 2026-01-03
**Scope:** Full codebase review (backend + frontend)

## Summary

| Area | Critical | Moderate | Minor |
|------|----------|----------|-------|
| Backend | 0 | 6 | 8 |
| Frontend | 0 | 4 | 5 |

No critical issues found. The codebase is functional and follows reasonable patterns for a family-use PWA.

---

## Backend Issues

### Moderate

#### 1. Missing Unique Constraint on Swipe Table

**File:** `backend/app/models.py:93-97`

```python
class Config:
    # Unique constraint: one swipe per member per movie
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
```

**Problem:** Comment says unique constraint exists, but only autoincrement is set. Constraint enforced in application code only.

**Recommendation:**
```python
__table_args__ = (
    UniqueConstraint('member_id', 'movie_id', name='unique_member_movie_swipe'),
)
```

---

#### 2. N+1 Query Problem in Movie Night Matching

**File:** `backend/app/routers/movie_night.py:49-77`

```python
for movie in filtered_movies:
    yes_swipes = db.query(Swipe).filter(...).all()
    for mid in member_ids:
        watched = db.query(MemberWatched).filter(...).first()
```

**Problem:** For each movie, queries swipes and potentially N watched records. With 50 movies and 5 members, this could be 50 + 250 = 300 queries.

**Recommendation:** Batch-load all swipes and watched records upfront:
```python
all_swipes = db.query(Swipe).filter(
    Swipe.movie_id.in_([m.movie_id for m in filtered_movies]),
    Swipe.member_id.in_(member_ids)
).all()

all_watched = db.query(MemberWatched).filter(
    MemberWatched.movie_id.in_([m.movie_id for m in filtered_movies]),
    MemberWatched.member_id.in_(member_ids)
).all()

# Build lookup dicts
swipes_by_movie = defaultdict(list)
for s in all_swipes:
    swipes_by_movie[s.movie_id].append(s)
```

---

#### 3. Overly Permissive CORS Configuration

**File:** `backend/app/main.py:18-24`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Problem:** `allow_origins=["*"]` with `allow_credentials=True` is a security anti-pattern.

**Recommendation:** Use environment-based configuration:
```python
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

#### 4. Unhandled Exceptions in External API Calls

**File:** `backend/app/services/tmdb.py:21-27`

```python
async def search_movies(self, query: str, page: int = 1) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(...)
        response.raise_for_status()  # Raises on 4xx/5xx
        return response.json()
```

**Problem:** Network errors and HTTP errors bubble up as unhandled 500 errors.

**Recommendation:** Add wrapper with proper error handling:
```python
async def _make_request(self, url: str, params: dict = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(503, "TMDB API timeout")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise HTTPException(502, f"TMDB API error: {e.response.status_code}")
```

---

#### 5. Silent Failure in Avatar Upload

**File:** `backend/app/routers/members.py:119-120`

```python
except Exception as e:
    raise HTTPException(status_code=400, detail="Failed to process image.")
```

**Problem:** Original exception `e` is caught but not logged. Debugging image issues is difficult.

**Recommendation:**
```python
import logging
logger = logging.getLogger(__name__)

except Exception as e:
    logger.error(f"Avatar processing failed: {e}", exc_info=True)
    raise HTTPException(status_code=400, detail="Failed to process image.")
```

---

#### 6. Deprecated datetime.utcnow() Usage

**Files:** `backend/app/models.py:30,57,58,73,88,107`

```python
created_at = Column(DateTime, default=datetime.utcnow)
```

**Problem:** `datetime.utcnow()` deprecated in Python 3.12+.

**Recommendation:**
```python
from datetime import datetime, timezone

created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

---

### Minor

#### 7. Duplicated Movie Serialization Code

**Files:**
- `backend/app/routers/movies.py:124-139,151-166`
- `backend/app/routers/swipes.py:91-112`
- `backend/app/routers/watchlist.py:34-55,182-202`
- `backend/app/routers/movie_night.py:100-119`
- `backend/app/routers/watched.py:56-80,194-215`

**Problem:** Same movie-to-dict conversion logic repeated 5+ times.

**Recommendation:** Create helper in `app/utils.py`:
```python
def movie_to_response(movie: Movie, tmdb_base: str = "https://image.tmdb.org/t/p/w500") -> dict:
    return {
        "id": movie.id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "overview": movie.overview,
        "release_date": movie.release_date,
        "poster_url": f"{tmdb_base}{movie.poster_path}" if movie.poster_path else None,
        "backdrop_url": f"{tmdb_base}{movie.backdrop_path}" if movie.backdrop_path else None,
        "vote_average": movie.vote_average,
        "genres": json.loads(movie.genres) if movie.genres else [],
        "runtime": movie.runtime,
        "content_rating": movie.content_rating,
        "rt_critic_score": movie.rt_critic_score,
        "trailer_url": movie.trailer_url,
        "created_at": movie.created_at,
    }
```

---

#### 8. Inconsistent async/sync Endpoints

**Files:** Various routers mix `async def` and `def`

**Problem:** Inconsistent pattern. Async only needed for async I/O (httpx calls).

**Recommendation:** Standardize: use `def` for database-only operations, `async def` only when calling async services.

---

#### 9. Missing Input Validation

**File:** `backend/app/schemas.py`

**Problem:** `MemberCreate.name` has no length constraint but `Member.name` is `String(100)`.

**Recommendation:**
```python
from pydantic import Field

class MemberCreate(BaseModel):
    name: str = Field(..., max_length=100)
```

---

#### 10. Missing Watchlist Router Tests

**Problem:** No dedicated `test_watchlist.py`. Watchlist functionality only indirectly tested.

**Recommendation:** Add `tests/test_watchlist.py` covering:
- Add to watchlist (manual, curated, trending sources)
- Remove from watchlist (soft delete)
- Duplicate handling
- RT score fetching

---

## Frontend Issues

### Moderate

#### 1. Duplicated Utility Functions

**`parseGenres` duplicated 3 times:**
- `frontend/src/pages/SwipeScreen.tsx:57-64`
- `frontend/src/pages/MovieNight.tsx:113-120`
- `frontend/src/components/MovieDetailCard.tsx:31-38`

**`getInitials` duplicated 3 times:**
- `frontend/src/pages/UserSelect.tsx:102-104`
- `frontend/src/pages/MovieNight.tsx:80-81`
- `frontend/src/components/BottomNav.tsx:136-138`

**`AVATAR_COLORS` duplicated 3 times:**
- `frontend/src/pages/UserSelect.tsx:10`
- `frontend/src/pages/MovieNight.tsx:16`
- `frontend/src/components/BottomNav.tsx:8`

**`TMDB_BASE_URL` duplicated 3 times:**
- `frontend/src/pages/SwipeScreen.tsx:18`
- `frontend/src/pages/MovieNight.tsx:17`
- `frontend/src/components/MovieDetailCard.tsx:6`

**Recommendation:** Create `frontend/src/utils/index.ts`:
```typescript
export const TMDB_BASE_URL = "https://image.tmdb.org/t/p/w500";

export const AVATAR_COLORS = [
  "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4",
  "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F",
];

export const getInitials = (name: string): string =>
  name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);

export const parseGenres = (genres: string | null): string[] => {
  if (!genres) return [];
  try {
    return JSON.parse(genres);
  } catch {
    return [];
  }
};

export const getAvatarUrl = (avatarPath: string | null): string | null => {
  if (!avatarPath) return null;
  const baseUrl = import.meta.env.VITE_API_URL?.replace("/api", "") || "";
  return `${baseUrl}${avatarPath}`;
};
```

---

#### 2. Unused API Client Exports

**File:** `frontend/src/api/client.ts`

**Unused exports:**
- `getMember` (line 26)
- `updateMember` (line 29)
- `deleteMember` (line 31)
- `getTrending` (line 44)
- `getMovie` (line 48)

**Recommendation:** Remove or document as reserved for future use. Dead exports increase maintenance burden.

---

#### 3. Inconsistent Avatar URL Construction

**Problem:** Different fallback behavior across files:
- `MovieNight.tsx` uses `'http://localhost:8000'` as fallback
- Others use `''` as fallback

**Recommendation:** Use shared `getAvatarUrl` utility (see #1 above).

---

#### 4. Missing Memoization

**File:** `frontend/src/pages/Watchlist.tsx:166-171`

```typescript
{watchlist
  ?.filter((entry) => {
    const memberSwipe = memberSwipes?.find(s => s.movie_id === entry.movie.id);
    return memberSwipe?.direction === 'yes';
  })
  .map((entry) => ...
```

**Problem:** O(n*m) filtering runs on every render.

**Recommendation:**
```typescript
const likedMovies = useMemo(() => {
  if (!watchlist || !memberSwipes) return [];
  const likedIds = new Set(
    memberSwipes.filter(s => s.direction === 'yes').map(s => s.movie_id)
  );
  return watchlist.filter(entry => likedIds.has(entry.movie.id));
}, [watchlist, memberSwipes]);
```

---

### Minor

#### 5. Large Component Files

| File | Lines |
|------|-------|
| `MovieNight.tsx` | 485 |
| `Watchlist.tsx` | 382 |
| `SwipeScreen.tsx` | 325 |

**Recommendation:** Extract subcomponents:
- `MovieNight.tsx` → `MemberSelector.tsx`, `MatchBrowser.tsx`, `WinnerCard.tsx`
- `Watchlist.tsx` → `SearchModal.tsx`, `DiscoverModal.tsx`

---

#### 6. Inline Helper Functions

**File:** `frontend/src/pages/MovieNight.tsx:80-120`

**Problem:** Pure functions like `getInitials`, `getColor`, `parseGenres` defined inside component, recreated each render.

**Recommendation:** Move pure utilities outside component or to shared utils.

---

#### 7. Non-null Assertions

**Examples:**
- `SwipeScreen.tsx:192` - `getSwipeQueue(memberId!, ...)`
- `Watchlist.tsx:52` - `getMemberWatched(memberId!)`

**Problem:** Bypasses TypeScript safety even though guarded by `enabled: !!memberId`.

**Recommendation:** Use conditional access or early returns.

---

## Priority Recommendations

### High Priority (fix soon)
1. Add unique constraint on Swipe table
2. Fix N+1 queries in movie night matching
3. Extract duplicated frontend utilities to shared file

### Medium Priority (next iteration)
4. Add error handling wrapper for external APIs
5. Add memoization to Watchlist filtering
6. Add logging to avatar upload error handling

### Low Priority (technical debt)
7. Standardize async/sync patterns
8. Add watchlist router tests
9. Extract large components into smaller pieces
10. Remove unused API exports

---

## Positive Observations

**Backend:**
- Clean SQLAlchemy ORM usage (no SQL injection risks)
- Good test coverage for core features
- Proper use of Pydantic schemas
- Well-organized router structure

**Frontend:**
- Excellent type safety (no `any` types)
- Good TanStack Query patterns with proper invalidation
- Consistent Framer Motion animations
- Clean hook design (`useCurrentMember`)
