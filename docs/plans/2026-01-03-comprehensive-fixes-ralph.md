# Comprehensive Fixes - Ralph Prompt

## Task

Fix all remaining code quality issues following the implementation plan in `docs/plans/2026-01-03-comprehensive-fixes-impl.md`.

## Iteration Protocol

Each iteration:
1. Read `docs/plans/2026-01-03-comprehensive-fixes-impl.md` to see checklist status
2. Find the FIRST unchecked `[ ]` item
3. Implement the fix exactly as specified
4. Run the test command specified for that item
5. If tests pass: mark item `[x]` in the impl file and commit
6. If tests fail: fix the issue before moving on

## Commands

```bash
# Backend tests (run from project root)
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest -v

# Specific test file
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest tests/test_<name>.py -v

# Frontend checks
cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build

# Docker validation
cd /Users/tim/Claude/Movie_picker && docker-compose config
```

## Commit Format

```
<type>(<scope>): <description>

Refs: docs/plans/2026-01-03-comprehensive-fixes-impl.md#<task-id>
```

**Types:** `fix`, `perf`, `refactor`, `test`, `chore`
**Scopes:** `backend`, `frontend`, `models`, `routers`, `services`, `utils`, `infra`

**Examples:**
```
perf(routers): add eager loading to watchlist endpoint

Refs: docs/plans/2026-01-03-comprehensive-fixes-impl.md#P1-1
```

```
test(backend): add movie search and trending endpoint tests

Refs: docs/plans/2026-01-03-comprehensive-fixes-impl.md#P4-1
```

## Phase Order

Complete phases in order:
1. **Phase 1: Backend Performance** (P1-1 through P1-4)
2. **Phase 2: Backend Quality** (P2-1 through P2-3)
3. **Phase 3: Frontend Patterns** (P3-1 through P3-8)
4. **Phase 4: Testing Coverage** (P4-1 through P4-4)
5. **Phase 5: Infrastructure** (P5-1 through P5-3)

## Completion Check

After marking the LAST item `[x]`:

1. Run full backend tests:
   ```bash
   cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest -v
   ```

2. Run frontend build:
   ```bash
   cd /Users/tim/Claude/Movie_picker/frontend && npm run lint && npm run build
   ```

3. Verify all checkboxes are marked in impl file

4. If ALL pass, output:
   ```
   <promise>COMPREHENSIVE FIXES COMPLETE</promise>
   ```

## Critical Rules

- **ONE fix per iteration** - keeps changes atomic and reviewable
- **ALWAYS run tests before marking complete** - never assume success
- **NEVER skip a failing test** - fix it or document why it can't be fixed
- **NEVER change functionality** - only improve code quality
- **If stuck for 2+ iterations** - add a note to the impl file and move to next item
- **Follow the implementation exactly** - don't over-engineer or add extras
- **Commit after each successful fix** - preserve progress

## Stuck Protocol

If a task cannot be completed after 2 attempts:

1. Add note under the task in impl file:
   ```markdown
   - [ ] P1-1: Task description
     > **BLOCKED:** [Reason why this cannot be completed]
     > **Attempted:** [What was tried]
   ```

2. Move to next task
3. Continue iteration

## File Locations

| Purpose | Path |
|---------|------|
| Implementation plan | `docs/plans/2026-01-03-comprehensive-fixes-impl.md` |
| Backend code | `backend/app/` |
| Backend tests | `backend/tests/` |
| Frontend code | `frontend/src/` |
| Docker config | `docker-compose.yml`, `deploy/docker-compose.yml` |
| Nginx config | `frontend/nginx.conf` |

## Example Iteration

```
Iteration 5:

1. Read impl file → Found first unchecked: P2-1 (Remove dead HTTPStatusError)

2. Open backend/app/services/omdb.py

3. Find lines 77-79, remove unused except clause

4. Run: pytest tests/test_ratings_and_trailers.py -v
   Result: 15 passed ✓

5. Mark [x] P2-1 in impl file

6. Commit:
   refactor(services): remove dead HTTPStatusError handler in OMDb

   Refs: docs/plans/2026-01-03-comprehensive-fixes-impl.md#P2-1

7. Exit iteration
```

## Verification at End

Before outputting completion promise, verify:

- [ ] All P1-x items marked [x]
- [ ] All P2-x items marked [x]
- [ ] All P3-x items marked [x]
- [ ] All P4-x items marked [x]
- [ ] All P5-x items marked [x]
- [ ] `pytest -v` shows 0 failures
- [ ] `npm run lint` shows 0 errors
- [ ] `npm run build` succeeds

Only then output: `<promise>COMPREHENSIVE FIXES COMPLETE</promise>`
