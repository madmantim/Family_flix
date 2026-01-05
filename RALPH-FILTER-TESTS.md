# Ralph Loop: Movie Night Filter Testing (Chrome Extension)

## Mission

Test the Movie Night filter feature using the Claude for Chrome browser extension. Work through all test cases until ALL pass, fixing any issues found in app code. Output `<promise>ALL TESTS PASSING</promise>` when complete.

## Prerequisites

Before starting:
1. **Servers running:**
   - Backend: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
   - Frontend: `cd frontend && npm run dev`
2. **Chrome extension connected** (run `/chrome` to verify)
3. **Test data exists** (2+ family members, 5+ movies with varied metadata)

## State Tracking

Track progress in `tests/e2e/filter_test_state.json`:
```json
{
  "iteration": 1,
  "tests_passed": ["TC-01", "TC-02"],
  "tests_failed": [],
  "tests_remaining": ["TC-03", ...],
  "last_error": null,
  "all_passed": false
}
```

## Each Iteration

### 1. Read State
- Check `tests/e2e/filter_test_state.json`
- If `all_passed: true` → output `<promise>ALL TESTS PASSING</promise>`
- Otherwise pick next test from `tests_remaining`

### 2. Execute Test in Browser

Use Chrome extension to:
1. Navigate to `http://localhost:5173/movie-night`
2. Perform test steps (click, type, verify elements)
3. Take screenshot if needed for verification
4. Check console for errors

**Example browser commands:**
```
Navigate to http://localhost:5173/movie-night
Click on the first family member to select them
Click the "Find Matches" button
Verify the filter section is visible with chips labeled "< 2hrs", "🍅 70%+", "no 18+", "New"
Take a screenshot
```

### 3. Analyze Results

- **PASSED:** Element found, behavior correct, no console errors
- **FAILED:** Element missing, wrong behavior, or console error

### 4. Fix Issues

If test fails:
- Identify root cause (CSS selector? Logic bug? Missing element?)
- Edit `frontend/src/pages/MovieNight.tsx` or `MovieNight.css`
- Run `cd frontend && npm run lint && npm run build` to verify
- Re-test in browser

### 5. Update State

After each test:
```bash
# Update filter_test_state.json with results
# If test passed, move to tests_passed
# If failed and fixed, re-run
# Git commit on progress
git add -A && git commit -m "test: TC-XX verified - [description]"
```

## Test Cases Quick Reference

See `docs/plans/movie-night-filter-tests.md` for full details.

| ID | Test | Key Actions |
|----|------|-------------|
| TC-01 | Filter section renders | Navigate, select member, find matches, verify `.filter-section` |
| TC-02 | Quick filter toggle | Click "< 2hrs" chip, verify `.active` class toggles |
| TC-03 | Genre filter toggle | Click genre chip, verify active state |
| TC-04 | Runtime filter logic | Activate "< 2hrs", verify only short movies shown |
| TC-05 | RT score filter logic | Activate "🍅 70%+", verify scores >= 70 |
| TC-06 | Content rating filter | Activate "no 18+", verify no adult movies |
| TC-07 | New movies filter | Activate "New", verify recent releases only |
| TC-08 | Genre OR logic | Select multiple genres, verify count increases |
| TC-09 | Quick filter AND logic | Combine filters, verify count decreases |
| TC-10 | Combined filters | Quick + genre, verify combined logic |
| TC-11 | Empty filter results | Over-filter to 0 results, verify empty state |
| TC-12 | Clear filters button | Click clear, verify all chips deactivated |
| TC-13 | Position indicator | Verify "X of Y (Z)" format when filtered |
| TC-14 | Progress bar | Verify bar reflects filtered count |
| TC-15 | Index reset | Browse to movie #5, filter, verify reset to #1 |
| TC-16 | Swipe with filters | Swipe through filtered results |
| TC-17 | Watch This flow | Select filtered movie, complete flow |
| TC-18 | Card layout | Verify side-by-side poster/info structure |
| TC-19 | Icon buttons | Click trailer (▶) and info (ℹ) buttons |
| TC-20 | Voter row | Verify avatars, labels display correctly |
| TC-21 | Member selection | Verify selection still works (regression) |
| TC-22 | Winner stage | Verify winner display (regression) |
| TC-23 | Completion stage | Verify mark watched flow (regression) |
| TC-24 | No genres | Verify genre row hidden if no genres |
| TC-25 | Swipe hint | Verify hint shown only when >1 movie |

## Browser Testing Pattern

For each test:
```
1. Navigate to http://localhost:5173/movie-night
2. [Setup] Select member(s), click Find Matches
3. [Action] Perform test action (click filter, swipe, etc.)
4. [Verify] Check element exists/state correct
5. [Console] Check for JavaScript errors
6. [Screenshot] Capture if needed for documentation
```

## Fixing App Issues

If browser test reveals bug:
1. Identify the issue from browser state/console
2. Read relevant code:
   - `frontend/src/pages/MovieNight.tsx` (logic)
   - `frontend/src/pages/MovieNight.css` (styling)
3. Make fix using Edit tool
4. Run lint/build:
   ```bash
   cd frontend && npm run lint && npm run build
   ```
5. Re-test in browser

## Completion

When all 25 tests pass:
1. Update state file with `all_passed: true`
2. Final commit:
   ```bash
   git add -A && git commit -m "test: all 25 filter tests verified via Chrome extension"
   ```
3. Output: `<promise>ALL TESTS PASSING</promise>`

## Critical Rules

1. **One test at a time** - Complete each test before moving on
2. **Screenshot failures** - Document issues visually
3. **Check console** - Look for JS errors after each action
4. **Verify fixes** - Always re-run lint/build after code changes
5. **Commit progress** - Git commit after each verified test
6. **No regressions** - Tests TC-21 through TC-23 verify existing functionality
