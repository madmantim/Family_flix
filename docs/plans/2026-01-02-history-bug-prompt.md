# Ralph Wiggum Prompt: Fix Watch History Bug

## Completion Promise
Output `<promise>HISTORY BUG FIXED</promise>` when ALL of the following are true:
1. The history bug is fixed
2. Backend tests pass (`pytest` from backend/)
3. Frontend builds without errors (`npm run build` from frontend/)
4. Manual verification confirms the routes work correctly

## Bug Description

### Route Ordering Bug in watched.py
**Problem**: The `/history/all` and `/history/stats` endpoints are unreachable because a wildcard route `/{member_id}` is defined BEFORE them.

**Current Route Order (BROKEN)**:
1. `@router.get("/{member_id}")` - Line 21 - catches "history" as member_id
2. `@router.post("/")` - Line 65
3. `@router.patch("/{member_id}/{movie_id}")` - Line 115
4. `@router.delete("/{member_id}/{movie_id}")` - Line 138
5. `@router.get("/history/all")` - Line 153 - NEVER REACHED
6. `@router.get("/history/stats")` - Line 217 - NEVER REACHED

**Result**: When frontend calls `/api/watched/history/all`, FastAPI matches it to `/{member_id}` with member_id="history", which fails because "history" is not an integer.

## Fix

Move the specific routes BEFORE the wildcard route. In FastAPI, more specific routes must be defined before generic path parameter routes.

**Correct Route Order**:
1. `@router.get("/history/all")` - specific, must come first
2. `@router.get("/history/stats")` - specific, must come first
3. `@router.get("/{member_id}")` - generic wildcard, must come last
4. Other routes can stay in their current positions

## Files to Modify

- `backend/app/routers/watched.py` - Reorder the route definitions

## Testing Requirements

1. Run `pytest` from backend/ - all tests must pass
2. Run `npm run build` from frontend/ - must compile without errors
3. Test the endpoints manually or via curl:
   - `curl http://localhost:8000/api/watched/history/all` should return watched movies
   - `curl http://localhost:8000/api/watched/history/stats` should return stats

## Implementation Notes

- Just move the function definitions - no logic changes needed
- Ensure the @router decorators and functions stay together when moving
- The order of routes in FastAPI determines matching precedence
