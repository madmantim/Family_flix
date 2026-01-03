# Watchlist Simplification - Ralph Loop Prompt

## Your Mission

Implement the Watchlist Simplification feature by following the implementation plan at `docs/plans/2026-01-03-watchlist-simplification-impl.md`.

**Design reference:** `docs/plans/2026-01-03-watchlist-simplification-design.md`

## What You're Building

Simplify the watchlist so that:
- **Y vote = "want to watch"** (replaces the confusing `would_rewatch` flag)
- **Watched state is decoupled from pool membership**
- **Movie Night ranking**: Y-count (desc) → N(W)-count (asc) → recency (desc)
- **Watchlist shows**: Only movies where user voted YES
- **History page**: Gets "want to watch again" button

## Iteration Protocol

Each iteration:

1. **Check progress** - Run `git log --oneline -15` to see completed commits
2. **Find next task** - Read the implementation plan, identify the next incomplete task
3. **Execute task** - Make the code changes as specified
4. **Verify** - Ensure no syntax errors (run linting if available)
5. **Commit** - Use the commit message format from the plan
6. **Assess completion** - Are ALL 11 tasks done?

## Task Checklist

Track these commits (check git log for completion):

- [ ] Task 1: `refactor: remove would_rewatch from MemberWatched model`
- [ ] Task 2: `refactor: remove would_rewatch from schemas`
- [ ] Task 3: `refactor: remove would_rewatch from watched router, add swipe flip`
- [ ] Task 4: `refactor: simplify Movie Night ranking to Y-count, N(W)-count, recency`
- [ ] Task 5: `refactor: remove would_rewatch from frontend types`
- [ ] Task 6: `refactor: remove would_rewatch from API client`
- [ ] Task 7: `refactor: remove watched toggle, filter watchlist by Y votes`
- [ ] Task 8: `refactor: remove watched toggle styles from Watchlist`
- [ ] Task 9: `feat: add 'want to watch again' button to History page`
- [ ] Task 10: `refactor: clean up MovieDetailCard, remove would_rewatch`
- [ ] Task 11: Delete DB (`rm backend/family_flix.db`) and verify app starts

## Completion Criteria

You are DONE when:

1. All 11 task commits exist in git history
2. Database has been deleted for fresh schema
3. No TypeScript/Python syntax errors
4. The app can start without crashes

When ALL criteria are met, output:

```
<promise>WATCHLIST SIMPLIFICATION COMPLETE</promise>
```

## Important Notes

- **Read the full implementation plan** - It has exact code snippets for each task
- **One task per iteration** - Don't try to do everything at once
- **Commit after each task** - This tracks your progress across iterations
- **Check git log first** - Don't redo completed work
- **If stuck** - Re-read the plan, the code is provided

## File Locations

| File | Purpose |
|------|---------|
| `backend/app/models.py` | MemberWatched model |
| `backend/app/schemas.py` | Pydantic schemas |
| `backend/app/routers/watched.py` | Watched endpoints |
| `backend/app/routers/movie_night.py` | Match algorithm |
| `frontend/src/types/index.ts` | TypeScript types |
| `frontend/src/api/client.ts` | API client functions |
| `frontend/src/pages/Watchlist.tsx` | Watchlist page |
| `frontend/src/pages/Watchlist.css` | Watchlist styles |
| `frontend/src/pages/History.tsx` | History page |
| `frontend/src/pages/History.css` | History styles |
| `frontend/src/components/MovieDetailCard.tsx` | Detail card component |

## Start

Read `docs/plans/2026-01-03-watchlist-simplification-impl.md` and begin with the first incomplete task.
