# Code Quality Fixes Implementation Plan

**Reference:** `docs/2026-01-03-code-quality-review.md`
**Goal:** Fix all identified issues while maintaining app functionality

## Pre-Flight Checks

Before each iteration:
1. Run `cd backend && source venv/bin/activate && pytest` - all tests must pass
2. Run `cd frontend && npm run lint` - no lint errors
3. Run `cd frontend && npm run build` - builds successfully

## Task Checklist

Track progress by checking items. **Do not mark complete until verified by tests.**

### Backend High Priority

- [x] **B1: Add unique constraint on Swipe table**
  - File: `backend/app/models.py`
  - Add: `UniqueConstraint('member_id', 'movie_id', name='unique_member_movie_swipe')`
  - Test: Existing tests should still pass (constraint enforced in app logic already)

- [x] **B2: Fix N+1 queries in movie night matching**
  - File: `backend/app/routers/movie_night.py`
  - Batch-load all swipes and watched records before the loop
  - Build lookup dicts: `swipes_by_movie[movie_id] = [swipes...]`
  - Test: `pytest tests/test_matching.py` must pass

### Backend Medium Priority

- [x] **B3: Add error handling wrapper for TMDB service**
  - File: `backend/app/services/tmdb.py`
  - Wrap httpx calls with try/except for TimeoutException and HTTPStatusError
  - Return None or raise HTTPException with appropriate status codes
  - Test: `pytest tests/test_ratings_and_trailers.py` must pass

- [ ] **B4: Add error handling wrapper for OMDb service**
  - File: `backend/app/services/omdb.py`
  - Same pattern as TMDB
  - Test: `pytest tests/test_ratings_and_trailers.py` must pass

- [ ] **B5: Add logging to avatar upload error handling**
  - File: `backend/app/routers/members.py`
  - Add `import logging` and `logger = logging.getLogger(__name__)`
  - Log exception before raising HTTPException
  - Test: `pytest tests/test_avatar.py` must pass

- [ ] **B6: Fix deprecated datetime.utcnow()**
  - Files: `backend/app/models.py` (all occurrences)
  - Change `datetime.utcnow` to `lambda: datetime.now(timezone.utc)`
  - Add `from datetime import timezone` import
  - Test: All backend tests must pass

### Backend Low Priority

- [ ] **B7: Extract movie serialization helper**
  - Create: `backend/app/utils.py` with `movie_to_response(movie: Movie) -> dict`
  - Update routers to use helper: `movies.py`, `swipes.py`, `watchlist.py`, `movie_night.py`, `watched.py`
  - Test: All backend tests must pass

- [ ] **B8: Add input validation to schemas**
  - File: `backend/app/schemas.py`
  - Add `Field(..., max_length=100)` to `MemberCreate.name`
  - Add appropriate length constraints to other string fields
  - Test: `pytest tests/test_members.py` must pass

- [ ] **B9: Create watchlist router tests**
  - Create: `backend/tests/test_watchlist.py`
  - Test: add to watchlist, remove from watchlist, duplicate handling
  - Coverage: At least 3 test cases

### Frontend High Priority

- [ ] **F1: Extract shared utilities**
  - Create: `frontend/src/utils/index.ts`
  - Move: `TMDB_BASE_URL`, `AVATAR_COLORS`, `getInitials`, `parseGenres`, `getAvatarUrl`
  - Update imports in: `SwipeScreen.tsx`, `MovieNight.tsx`, `MovieDetailCard.tsx`, `UserSelect.tsx`, `BottomNav.tsx`
  - Test: `npm run build` and `npm run lint` must pass

### Frontend Medium Priority

- [ ] **F2: Add memoization to Watchlist filtering**
  - File: `frontend/src/pages/Watchlist.tsx`
  - Wrap liked movies filter in `useMemo`
  - Use Set for O(1) lookups instead of O(n) find
  - Test: `npm run build` must pass

- [ ] **F3: Remove unused API exports**
  - File: `frontend/src/api/client.ts`
  - Remove: `getMember`, `updateMember`, `deleteMember`, `getTrending`, `getMovie`
  - Or add `// @ts-expect-error Reserved for future use` comment
  - Test: `npm run build` must pass, verify no import errors

### Frontend Low Priority

- [ ] **F4: Move pure functions outside MovieNight component**
  - File: `frontend/src/pages/MovieNight.tsx`
  - Move `getInitials`, `getColor`, `parseGenres` outside component (or use from utils)
  - Test: `npm run build` must pass

## Verification Protocol

After ALL tasks complete:

1. **Backend tests:** `cd backend && pytest -v` - ALL must pass
2. **Frontend lint:** `cd frontend && npm run lint` - No errors
3. **Frontend build:** `cd frontend && npm run build` - Successful
4. **Spot check:** Review git diff to ensure no unintended changes

## Success Criteria

All of the following must be true:
- [ ] All checklist items marked complete
- [ ] `pytest` passes with 0 failures
- [ ] `npm run lint` passes with 0 errors
- [ ] `npm run build` succeeds
- [ ] No functionality removed or broken

## Iteration Strategy

1. **Start with high priority items** - they have the most impact
2. **Run tests after each change** - catch regressions immediately
3. **Commit after each successful fix** - preserve progress
4. **If tests fail, fix before moving on** - don't accumulate debt

## Notes

- Do NOT refactor beyond what's specified
- Do NOT add new features
- Do NOT change API contracts
- Preserve all existing behavior
