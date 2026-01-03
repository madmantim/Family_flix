# Ralph Loop: E2E Browser Testing for Family Flix Picker

## Purpose

This prompt drives iterative browser E2E testing using Claude for Chrome. Each iteration:
1. Checks current test progress state
2. Runs next pending tests
3. On failure: dispatches fix agent, marks test for re-run
4. On success: marks test complete, proceeds to next
5. Continues until all tests pass

---

## Instructions

You are executing E2E browser tests for the Family Flix Picker application.

### Before Starting

1. Read the test plan: `docs/plans/browser-e2e-tests.md`
2. Read current progress: `docs/plans/.e2e-test-state.json`
3. If state file doesn't exist, create it with initial state

### State File Structure

```json
{
  "iteration": 1,
  "phase": "setup",
  "tests": {
    "M-01": { "status": "pending", "attempts": 0 },
    "M-02": { "status": "pending", "attempts": 0 }
  },
  "failures": [],
  "fixes_dispatched": [],
  "completed_count": 0,
  "total_count": 47
}
```

Status values: `pending`, `running`, `passed`, `failed`, `fixed-pending-retest`

### Each Iteration

#### Step 1: Load State
Read `.e2e-test-state.json`. Increment `iteration` counter.

#### Step 2: Ensure App is Running
Check if frontend (localhost:5173) and backend (localhost:8000) are accessible.
If not running:
```bash
# Start backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

# Start frontend
cd frontend && npm run dev &
```
Wait for both to be ready.

#### Step 3: Get Browser Context
Use `mcp__claude-in-chrome__tabs_context_mcp` to get/create tab.
Navigate to `http://localhost:5173` if not already there.

#### Step 4: Find Next Test
Priority order:
1. Tests with status `fixed-pending-retest` (verify fixes work)
2. Tests with status `pending` in phase order

#### Step 5: Execute Test
For each test:
1. Set status to `running` in state file
2. Execute test steps using browser tools:
   - `navigate` - go to URLs
   - `find` - locate elements
   - `computer` - click, type, screenshot
   - `form_input` - fill forms
   - `read_page` - verify DOM state
   - `read_console_messages` - check for errors
   - `read_network_requests` - verify API calls
3. Take screenshot at key verification points
4. Compare actual vs expected outcomes

#### Step 6: Record Result

**On Pass:**
```json
{ "status": "passed", "attempts": N, "verified_at": "timestamp" }
```
Increment `completed_count`. Move to next test.

**On Fail:**
```json
{
  "status": "failed",
  "attempts": N,
  "error": "description",
  "console_errors": [...],
  "expected": "...",
  "actual": "..."
}
```
Add to `failures` array. Dispatch fix agent (Step 7).

#### Step 7: Dispatch Fix Agent (On Failure)

Use the `Task` tool with `subagent_type="general-purpose"` to fix the bug:

```
Prompt for fix agent:
---
E2E Test [TEST_ID] failed.

**Test Description**: [from test plan]
**Expected**: [expected behavior]
**Actual**: [actual behavior]
**Console Errors**: [if any]
**Network Failures**: [if any]

Investigate and fix the bug. Check:
1. Frontend code in src/pages/ and src/components/
2. Backend code in app/routers/ and app/services/
3. API client in src/api/client.ts

After fixing, run relevant pytest tests to verify backend.
Commit fix with message: "fix: [TEST_ID] - [brief description]"
---
```

After fix dispatched:
- Add to `fixes_dispatched` array
- Set test status to `fixed-pending-retest`

#### Step 8: Update State
Write updated state to `.e2e-test-state.json`.

#### Step 9: Check Completion

If `completed_count === total_count` and all tests show `passed`:
```
<promise>ALL E2E TESTS PASSED</promise>
```

If max iterations (50) reached with failures:
```
<promise>MAX ITERATIONS - MANUAL REVIEW NEEDED</promise>
```

Otherwise: Continue to next iteration.

---

## Test Execution Details

### Browser Automation Patterns

**Navigate and verify page load:**
```
1. navigate to URL
2. wait 2 seconds
3. read_page to verify expected elements
4. screenshot for visual verification
```

**Click element by text/role:**
```
1. find "button with text X"
2. computer action=left_click ref=found_ref
```

**Fill form:**
```
1. find "input field for X"
2. form_input ref=found_ref value="test value"
```

**Swipe gesture (for movie cards):**
```
1. find "movie card"
2. computer action=left_click_drag start_coordinate=[card_center] coordinate=[right_edge]
```

**Verify text content:**
```
1. read_page
2. Check accessibility tree contains expected text
```

**Check for errors:**
```
1. read_console_messages pattern="error|Error|exception"
2. If matches found, test fails
```

### Cross-User Testing Pattern

For tests requiring multiple users (X-01 through X-04):
1. Complete actions as User1
2. Navigate to `/` (home)
3. Select different user
4. Complete actions as User2
5. Verify combined state

### Content Filter Testing

For content filter tests (S-08, N-07):
1. Ensure KidUser exists with `content_filter: "Kids"`
2. Log in as KidUser
3. Verify only age-appropriate content shown

---

## Recovery Procedures

### If Browser Tab Lost
Call `tabs_context_mcp` to get fresh tab context. Create new tab if needed.

### If App Crashed
Restart backend and frontend. Reset database if corruption suspected:
```bash
cd backend && rm family_flix.db && python -c "from app.database import init_db; init_db()"
```
Restart from Phase 1 (member creation).

### If Test Flaky
Mark test with `flaky: true`. Re-run up to 3 times before marking failed.

---

## Completion Criteria

All tests must pass:
- 7 Member tests (M-01 to M-07)
- 9 Discovery tests (D-01 to D-09)
- 9 Swipe tests (S-01 to S-09)
- 4 Cross-user tests (X-01 to X-04)
- 8 Movie night tests (N-01 to N-08)
- 4 History tests (H-01 to H-04)
- 4 Watchlist tests (W-01 to W-04)
- 6 UI tests (U-01 to U-06)
- 3 Error tests (E-01 to E-03)

**Total: 54 tests**

When complete, output:
```
<promise>ALL E2E TESTS PASSED</promise>
```

---

## State File Location

`/Users/tim/Claude/Movie_picker/docs/plans/.e2e-test-state.json`
