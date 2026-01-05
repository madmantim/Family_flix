# Ralph Loop: Movie Night Filter Testing

## Mission

Implement, run, and fix Playwright tests for the Movie Night filter feature until ALL tests pass. Work autonomously through the test cases defined in `docs/plans/movie-night-filter-tests.md`.

## State Tracking

Use `tests/e2e/filter_test_state.json` to track progress:
```json
{
  "iteration": 1,
  "tests_passed": [],
  "tests_failed": [],
  "tests_remaining": ["TC-01", "TC-02", ...],
  "last_error": null,
  "all_passed": false
}
```

## Each Iteration

### 1. Check State
- Read `tests/e2e/filter_test_state.json`
- If `all_passed: true`, output `<promise>ALL TESTS PASSING</promise>` and exit
- Otherwise, pick the next test from `tests_remaining` or retry a failed test

### 2. Implement/Fix Test
- Create or update `tests/e2e/test_movie_night_filters.py`
- Reference `docs/plans/movie-night-filter-tests.md` for test specs
- Use the webapp-testing skill pattern:
  ```python
  from playwright.sync_api import sync_playwright

  with sync_playwright() as p:
      browser = p.chromium.launch(headless=True)
      page = browser.new_page()
      page.goto('http://localhost:5173/movie-night')
      page.wait_for_load_state('networkidle')
      # ... test logic
      browser.close()
  ```

### 3. Run Test
```bash
python scripts/with_server.py \
  --server "cd backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000" --port 8000 \
  --server "cd frontend && npm run dev" --port 5173 \
  -- python tests/e2e/test_movie_night_filters.py
```

### 4. Analyze Results
- If PASSED: Move test to `tests_passed`, update state file
- If FAILED:
  - Capture error in `last_error`
  - Fix the issue (could be test code OR app code)
  - If app code changed, run `npm run lint` and `npm run build` to verify
  - Keep test in `tests_remaining` for next iteration

### 5. Update State
- Write updated state to `tests/e2e/filter_test_state.json`
- If all 25 tests passed, set `all_passed: true`

## Critical Rules

1. **Never break existing functionality** - If you modify app code, run full lint/build check
2. **Screenshot on failure** - Save to `/tmp/failure_tc_XX.png` for debugging
3. **Incremental progress** - One test at a time, commit working tests
4. **Git commits** - After each passing test or significant fix:
   ```bash
   git add -A && git commit -m "test(e2e): TC-XX passing - [description]"
   ```

## Test Prerequisites

Before first test run, ensure test data exists:
- At least 2 family members in database
- At least 5 movies in watchlist with varied:
  - Runtimes (mix of <120 and >=120 min)
  - RT scores (mix of >=70%, <70%, and null)
  - Content ratings (all_ages, teen, mature, adult)
  - Years (some 2025-2026, some older)
  - Genres (at least 3 different genres)

If data is missing, seed it via API calls first.

## Completion Signal

When ALL 25 tests pass:
```
<promise>ALL TESTS PASSING</promise>
```

## Files Reference

| File | Purpose |
|------|---------|
| `docs/plans/movie-night-filter-tests.md` | Full test specifications |
| `tests/e2e/test_movie_night_filters.py` | Test implementation |
| `tests/e2e/filter_test_state.json` | Progress tracking |
| `frontend/src/pages/MovieNight.tsx` | Component under test |
| `frontend/src/pages/MovieNight.css` | Styles under test |

## Debugging Tips

- If element not found: wait for `networkidle`, take screenshot, inspect selectors
- If filter logic wrong: check `filteredMatches` computation in MovieNight.tsx
- If layout broken: check CSS classes match between TSX and CSS
- If servers won't start: check ports 8000/5173 not already in use
