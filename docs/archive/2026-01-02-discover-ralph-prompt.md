# Ralph Loop Prompt: Discover Feature Implementation

## Your Mission

Implement the Discover feature for the Watchlist screen following the detailed implementation plan at `docs/plans/2026-01-02-discover-feature-implementation.md`.

## Context

- **Design document**: `docs/plans/2026-01-02-discover-feature-design.md`
- **Implementation plan**: `docs/plans/2026-01-02-discover-feature-implementation.md`
- **Project**: Family Flix Picker - movie voting PWA
- **Feature**: Add "Discover" button to Watchlist showing Popular and Highly Rated movies available for home viewing

## Execution Instructions

1. **Read the implementation plan** at `docs/plans/2026-01-02-discover-feature-implementation.md`

2. **Check your progress** by examining:
   - Git log: `git log --oneline -10`
   - Current file state of modified files
   - Test results: `cd backend && python -m pytest -v`
   - Frontend build: `cd frontend && npm run build`

3. **Execute tasks in order** (Task 1 through Task 6):
   - Follow TDD: write test first, verify it fails, implement, verify it passes
   - Commit after each task
   - Move to the next incomplete task

4. **Skip completed tasks** - Check git history and file contents to identify what's already done

5. **Fix any issues** - If tests fail or build breaks, debug and fix before proceeding

## Success Criteria

All of the following must be true:
- [ ] `cd backend && python -m pytest` - ALL tests pass
- [ ] `cd frontend && npm run build` - Build succeeds
- [ ] `cd frontend && npm run lint` - No errors
- [ ] `/movies/discover?tab=popular` endpoint returns movies
- [ ] `/movies/discover?tab=highly-rated` endpoint returns movies
- [ ] Discover button visible in Watchlist header
- [ ] Discover modal opens with two working tabs
- [ ] Tapping movie adds to watchlist and removes from discover grid

## Completion Promise

When ALL success criteria are met, output:

<promise>DISCOVER FEATURE COMPLETE</promise>

## Important Notes

- Do NOT output the promise until the feature is fully working
- Run tests frequently to catch issues early
- Read the implementation plan carefully - it has exact code to use
- Check existing code before modifying to understand current patterns
- Backend runs on port 8000, frontend on port 5173
