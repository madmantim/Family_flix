# Movie Night Filter Tests

## Test Environment

- **Frontend URL:** http://localhost:5173
- **Backend URL:** http://localhost:8000
- **Browser:** Chromium (headless via Playwright)

## Prerequisites

Before running tests, ensure:
1. Backend server running: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. Frontend dev server running: `cd frontend && npm run dev`
3. Database has test data (at least 2 family members, 5+ movies in watchlist with varied metadata)

## Test Data Requirements

For comprehensive filter testing, the watchlist should contain movies with:
- Various runtimes (some < 120 min, some >= 120 min)
- Various RT scores (some >= 70%, some < 70%, some null)
- Various content ratings (all_ages, teen, mature, adult)
- Various release years (some from current/last year, some older)
- Various genres (at least 3 different genres represented)

## Test Cases

### TC-01: Filter Section Renders
**Description:** Verify filter chips appear on browse stage
**Steps:**
1. Navigate to Movie Night page (`/movie-night`)
2. Select at least one member
3. Click "Find Matches"
4. Verify filter section is visible

**Expected:**
- Quick filter row visible with 4 chips: "< 2hrs", "🍅 70%+", "no 18+", "New"
- Genre row visible (if matches have genres)
- All chips initially inactive (no `active` class)

**Selectors:**
- Filter section: `.filter-section`
- Quick filter chips: `.filter-row:not(.genres) .filter-chip`
- Genre chips: `.filter-row.genres .filter-chip`

---

### TC-02: Quick Filter Toggle
**Description:** Verify quick filter chips toggle on/off
**Steps:**
1. Navigate to browse stage with matches
2. Click "< 2hrs" chip
3. Verify chip becomes active
4. Click "< 2hrs" chip again
5. Verify chip becomes inactive

**Expected:**
- First click adds `active` class
- Second click removes `active` class
- Filter state persists during browsing

**Selectors:**
- Runtime filter: `.filter-chip:has-text("< 2hrs")`
- Active state: `.filter-chip.active`

---

### TC-03: Genre Filter Toggle
**Description:** Verify genre chips toggle on/off
**Steps:**
1. Navigate to browse stage with matches
2. Click first genre chip
3. Verify chip becomes active
4. Click same genre chip again
5. Verify chip becomes inactive

**Expected:**
- Genre chips have `genre-chip` class
- Active genre chips have both `genre-chip` and `active` classes

**Selectors:**
- Genre chips: `.filter-chip.genre-chip`
- Active genre: `.filter-chip.genre-chip.active`

---

### TC-04: Runtime Filter Logic
**Description:** Verify "< 2hrs" filter excludes movies >= 120 min
**Steps:**
1. Navigate to browse stage
2. Note total match count in position indicator
3. Click "< 2hrs" filter
4. Verify filtered count is <= original count
5. Browse through filtered movies
6. Verify all visible movies have runtime < 120 min (or no runtime shown)

**Expected:**
- Position indicator shows filtered count: "X of Y (Z)" format
- Only movies under 2 hours shown
- Movies with null runtime are excluded

**Selectors:**
- Position indicator: `.position-indicator`
- Runtime in card: `.meta-line span` containing "min"

---

### TC-05: RT Score Filter Logic
**Description:** Verify "🍅 70%+" filter excludes movies with score < 70
**Steps:**
1. Navigate to browse stage
2. Click "🍅 70%+" filter
3. Browse through filtered movies
4. Verify all visible movies have RT score >= 70%

**Expected:**
- Only movies with RT score >= 70 shown
- Movies with null RT score are excluded

**Selectors:**
- RT score filter: `.filter-chip:has-text("🍅 70%+")`
- RT score in card: `.rt-score`

---

### TC-06: Content Rating Filter Logic
**Description:** Verify "no 18+" filter excludes adult-rated movies
**Steps:**
1. Navigate to browse stage
2. Click "no 18+" filter
3. Browse through filtered movies
4. Verify no movies show "18+" or "Adult" rating

**Expected:**
- Adult content excluded
- Mature content (if present) still shown

**Selectors:**
- Rating filter: `.filter-chip:has-text("no 18+")`
- Rating badge: `.rating-badge`

---

### TC-07: New Movies Filter Logic
**Description:** Verify "New" filter shows only recent releases
**Steps:**
1. Navigate to browse stage
2. Click "New" filter
3. Browse through filtered movies
4. Verify all visible movies are from current or previous year

**Expected:**
- Only movies from 2025-2026 shown (assuming current year is 2026)
- Older movies excluded

**Selectors:**
- New filter: `.filter-chip:has-text("New")`
- Year in title: `.browse-info h2 .year`

---

### TC-08: Genre Filter Logic (OR)
**Description:** Verify genre filters use OR logic
**Steps:**
1. Navigate to browse stage
2. Click "Action" genre (if available)
3. Note filtered count
4. Click "Comedy" genre (if available)
5. Verify filtered count >= count with single genre

**Expected:**
- Multiple genres = show movies matching ANY selected genre
- Count increases or stays same when adding genres

---

### TC-09: Combined Filters (AND)
**Description:** Verify quick filters combine with AND logic
**Steps:**
1. Navigate to browse stage
2. Click "< 2hrs" filter, note count
3. Click "🍅 70%+" filter
4. Verify count decreased or stayed same

**Expected:**
- Combining quick filters narrows results
- Each added filter is more restrictive

---

### TC-10: Quick + Genre Combined
**Description:** Verify quick filters AND genre filters work together
**Steps:**
1. Navigate to browse stage
2. Activate "< 2hrs" quick filter
3. Activate a genre filter
4. Verify results match BOTH criteria

**Expected:**
- Movies must pass quick filter AND match genre
- Combined logic: (QuickFilters) AND (GenreFilters)

---

### TC-11: Empty Filter Results
**Description:** Verify empty state when all movies filtered out
**Steps:**
1. Navigate to browse stage
2. Activate multiple restrictive filters until no matches
3. Verify empty state appears

**Expected:**
- Message: "No movies match these filters"
- "Clear Filters" button visible
- Card container shows empty state, not broken UI

**Selectors:**
- Empty state: `.empty-filtered`
- Clear button: `.clear-filters-btn`

---

### TC-12: Clear Filters Button
**Description:** Verify Clear Filters restores all matches
**Steps:**
1. Activate filters to get empty or reduced results
2. Click "Clear Filters" button
3. Verify all matches restored

**Expected:**
- All filter chips deactivated
- Original match count restored
- Index reset to first movie

---

### TC-13: Position Indicator Updates
**Description:** Verify position indicator reflects filtered count
**Steps:**
1. Navigate to browse stage, note indicator (e.g., "1 of 12")
2. Activate a filter that reduces count
3. Verify indicator format changes to "X of Y (Z)"

**Expected:**
- Unfiltered: "1 of 12"
- Filtered: "1 of 8 (12)" - filtered count in gold, total in parentheses

**Selectors:**
- Indicator: `.position-indicator`
- Filtered span: `.position-indicator .filtered`

---

### TC-14: Progress Bar Updates
**Description:** Verify progress bar reflects filtered list length
**Steps:**
1. Navigate to browse stage with filters active
2. Verify progress bar width corresponds to filtered count
3. Click on progress bar to navigate
4. Verify navigation works within filtered results

**Expected:**
- Progress bar shows position within filtered results
- Clicking progress bar navigates within filtered list

---

### TC-15: Index Reset on Filter Change
**Description:** Verify browsing index resets when filters change
**Steps:**
1. Browse to movie #5 of 10
2. Activate a filter
3. Verify index resets to first movie

**Expected:**
- Always show first filtered movie after filter change
- Prevents out-of-bounds errors

---

### TC-16: Swipe Navigation with Filters
**Description:** Verify swipe still works with filtered results
**Steps:**
1. Activate filters to reduce to 3 movies
2. Swipe left to advance
3. Verify navigation through filtered movies
4. Verify cannot swipe past last filtered movie

**Expected:**
- Swipe navigates through filtered list only
- Bounds respected (can't go past filtered list length)

**Selectors:**
- Browse card: `.browse-card`

---

### TC-17: Watch This with Filters Active
**Description:** Verify "Watch This" works from filtered results
**Steps:**
1. Activate filters
2. Click "Watch This" on a filtered movie
3. Verify winner stage shows correct movie
4. Complete the flow

**Expected:**
- Correct movie passed to winner stage
- Flow completes normally
- Filters reset after completion

---

### TC-18: Card Layout - Side by Side
**Description:** Verify new card layout renders correctly
**Steps:**
1. Navigate to browse stage
2. Inspect card structure

**Expected:**
- Poster on left (~120px width)
- Info section on right
- Title, metadata, icon buttons visible
- Voter row below poster/info block
- Synopsis at bottom

**Selectors:**
- Card top section: `.browse-card-top`
- Poster: `.browse-poster`
- Info: `.browse-info`
- Meta stack: `.meta-stack`
- Icon buttons: `.icon-buttons`
- Voter row: `.voter-row`

---

### TC-19: Icon Buttons Functional
**Description:** Verify Trailer and More icon buttons work
**Steps:**
1. Navigate to browse stage
2. Click trailer button (▶) if present
3. Verify new tab opens with trailer
4. Click info button (ℹ)
5. Verify TMDB page opens

**Expected:**
- Trailer button opens YouTube/trailer URL
- Info button opens TMDB movie page
- Buttons have correct styling (trailer is red-tinted)

**Selectors:**
- Trailer button: `.icon-btn.trailer`
- Info button: `.icon-btn:not(.trailer)`

---

### TC-20: Voter Row Display
**Description:** Verify voter avatars and labels render correctly
**Steps:**
1. Navigate to browse stage
2. Inspect voter row

**Expected:**
- Voter icon (✓ for full match, 👍 for partial)
- Avatar stack with overlapping circles
- Label: "Everyone!" (green) or "X/Y voted yes"

**Selectors:**
- Voter row: `.voter-row`
- Voter icon: `.voter-icon`
- Voter avatars: `.voter-avatars`
- Voter label: `.voter-label`
- Everyone label: `.voter-label.everyone`

---

### TC-21: No Regression - Member Selection
**Description:** Verify member selection still works
**Steps:**
1. Navigate to Movie Night page
2. Click on family members to select/deselect
3. Verify selection state toggles correctly

**Expected:**
- Members can be selected/deselected
- Selected members show checkmark
- "Find Matches" enabled when at least 1 selected

---

### TC-22: No Regression - Winner Stage
**Description:** Verify winner stage displays correctly
**Steps:**
1. Navigate through full flow to winner stage
2. Verify movie poster, title, year displayed
3. Verify "Mark as Watched" and "Done" buttons work

**Expected:**
- Winner celebration animation plays
- Movie details correct
- Both buttons functional

---

### TC-23: No Regression - Completion Stage
**Description:** Verify completion (who watched) stage works
**Steps:**
1. From winner stage, click "Mark as Watched"
2. Select watchers
3. Click "Confirm Watched"

**Expected:**
- All family members listed with checkboxes
- Selected members pre-checked (those present)
- Confirm button marks movie as watched
- Flow resets to selection stage

---

### TC-24: Genre Row Hidden When No Genres
**Description:** Verify genre row doesn't render if no genres in matches
**Steps:**
1. Ensure test data has movies without genres
2. Navigate to browse stage

**Expected:**
- If all matches lack genres, genre row not rendered
- No empty genre row visible

---

### TC-25: Swipe Hint Visibility
**Description:** Verify swipe hint shows appropriately
**Steps:**
1. Navigate with 1 filtered result
2. Verify swipe hint hidden
3. Navigate with 2+ filtered results
4. Verify swipe hint visible

**Expected:**
- "← swipe to browse →" only shown when > 1 movie
- Hidden when only 1 movie in filtered results

---

## Regression Test Summary

| Area | Tests |
|------|-------|
| Filter UI | TC-01, TC-02, TC-03 |
| Filter Logic | TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10 |
| Empty/Edge Cases | TC-11, TC-12, TC-24, TC-25 |
| Navigation | TC-13, TC-14, TC-15, TC-16 |
| Integration | TC-17 |
| Card Layout | TC-18, TC-19, TC-20 |
| Regression | TC-21, TC-22, TC-23 |

## Test Script Template

```python
from playwright.sync_api import sync_playwright
import sys

def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to app
            page.goto('http://localhost:5173/movie-night')
            page.wait_for_load_state('networkidle')

            # TC-XX: Description
            # ... test implementation ...

            print("✅ TC-XX: PASSED")

        except Exception as e:
            print(f"❌ TC-XX: FAILED - {e}")
            page.screenshot(path='/tmp/failure_tc_xx.png')

        finally:
            browser.close()

if __name__ == "__main__":
    run_tests()
```
