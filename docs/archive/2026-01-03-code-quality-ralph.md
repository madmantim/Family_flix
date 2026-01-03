# Code Quality Fixes - Ralph Prompt

## Task

Fix all code quality issues documented in `docs/2026-01-03-code-quality-review.md` following the implementation plan in `docs/plans/2026-01-03-code-quality-fixes-impl.md`.

## Iteration Protocol

Each iteration:
1. Read `docs/plans/2026-01-03-code-quality-fixes-impl.md` to see checklist status
2. Find the FIRST unchecked `[ ]` item
3. Implement the fix
4. Run the specified tests for that item
5. If tests pass: mark item `[x]` in the impl file and commit
6. If tests fail: fix the issue before moving on

## Commands

```bash
# Backend tests
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest -v

# Frontend checks
cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build
```

## Commit Format

```
fix(<scope>): <description>

Refs: docs/2026-01-03-code-quality-review.md
```

Scopes: `backend`, `frontend`, `models`, `services`, `routers`, `utils`

## Completion Check

When ALL items in the impl checklist are marked `[x]`:

1. Run full backend tests: `cd backend && pytest -v`
2. Run frontend build: `cd frontend && npm run lint && npm run build`
3. If both pass, output: `<promise>CODE QUALITY FIXES COMPLETE</promise>`

## Critical Rules

- ONE fix per iteration (keeps changes atomic)
- ALWAYS run tests before marking complete
- NEVER skip a failing test
- NEVER change functionality, only improve code quality
- If stuck on an item for 2+ iterations, add a note and move to next item
