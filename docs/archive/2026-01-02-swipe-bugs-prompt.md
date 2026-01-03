# Ralph Wiggum Prompt: Fix Swipe Screen Bugs

## Completion Promise
Output `<promise>SWIPE BUGS FIXED</promise>` when ALL of the following are true:
1. All three bugs are fixed
2. Backend tests pass (`pytest` from backend/)
3. Frontend builds without errors (`npm run build` from frontend/)
4. Manual verification confirms the logic is correct

## Bugs to Fix

### Bug 1: Batch Limit Creates False "All Caught Up" State
**Problem**: Queue only fetches 20 movies at a time. When you swipe through all 20, it shows "All caught up!" even if there are more unswiped movies. Only by navigating away and returning do you get the next batch.

**Fix**: Auto-fetch more movies when approaching the end of the current batch. When current batch is exhausted but more exist, show "Loading more..." not "All caught up!"

### Bug 2: Movies Get Skipped (Race Condition)
**Problem**: After each swipe:
1. `currentIndex` increments from 0 to 1
2. Query is invalidated, triggering a refetch
3. UI immediately shows `movies[1]` (movie B)
4. Refetch completes with array `[B, C, D, ...]` (without swiped movie A)
5. But `currentIndex` is still 1, so UI shows `movies[1]` = C
6. Movie B was skipped!

**Fix**: Either:
- Option A: Don't refetch after every swipe. Just track swiped IDs locally and filter them out. Only refetch when batch is exhausted.
- Option B: Use optimistic updates to remove the swiped movie from the cache, and reset currentIndex appropriately.
- Option C: Don't use currentIndex at all - filter out swiped movies from the array directly.

Recommended: Option A or C - simplest and most reliable.

### Bug 3: Header Counter is Misleading
**Problem**: Header shows `total_unswiped` (true count) but card stack only has 20 movies. Creates confusion.

**Fix**: Either:
- Show count of remaining in current batch, with indicator of total
- Or ensure the batch auto-extends so the counter is always accurate

## Files to Modify

### Frontend
- `frontend/src/pages/SwipeScreen.tsx` - Main swipe logic
- `frontend/src/api/client.ts` - If API changes needed

### Backend (if needed)
- `backend/app/routers/swipes.py` - Queue endpoint

## Testing Requirements

1. Run `pytest` from backend/ - all tests must pass
2. Run `npm run build` from frontend/ - must compile without errors
3. Verify logic manually:
   - If there are 50 unswiped movies, swiping through them should eventually show all 50, not just 20
   - No movies should be skipped
   - Counter should accurately reflect remaining movies
   - "All caught up!" should only show when truly no movies left

## Implementation Notes

- Keep the solution simple - don't over-engineer
- Maintain the existing UI/UX (swipe gestures, animations, etc.)
- The `total_unswiped` from the API is the source of truth for how many movies remain
- Consider whether to track swiped IDs in component state or rely on React Query cache

## Current State Check

Before making changes, verify current behavior:
1. Read `frontend/src/pages/SwipeScreen.tsx`
2. Understand the current data flow
3. Identify exactly where each bug manifests
