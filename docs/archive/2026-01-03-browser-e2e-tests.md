# Family Flix Picker - Browser E2E Testing Plan

## Overview

This document defines comprehensive end-to-end browser tests for Family Flix Picker using Claude for Chrome browser automation. Tests cover all functionality and cross-user scenarios.

**Testing Approach**: Use Claude Code's browser automation tools (`mcp__claude-in-chrome__*`) to interact with the running application, validate UI state, and verify cross-user data flows.

**Prerequisites**:
- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:5173`
- Fresh/clean database state

---

## Test Suites

### Suite 1: Member Management (UserSelect Page)

| Test ID | Test Name | Steps | Success Criteria |
|---------|-----------|-------|------------------|
| M-01 | Create member | Navigate to `/`, click "+" button, enter name "TestUser1", submit | Member appears in member list with default avatar |
| M-02 | Create second member | Click "+", enter name "TestUser2", submit | Two members visible in list |
| M-03 | Create child member | Click "+", enter name "KidUser", set content filter to "Kids", submit | Member created with restricted content filter |
| M-04 | Select member | Click on "TestUser1" avatar | Navigates to `/swipe`, member name shown in header |
| M-05 | Edit member name | Long-press member avatar, change name to "RenamedUser", save | Name updates in UI |
| M-06 | Avatar upload | Long-press member, click avatar, upload test image | Avatar displays uploaded image (256x256) |
| M-07 | Duplicate name prevention | Try creating member with existing name | Error message shown, member not created |

### Suite 2: Movie Discovery & Search (Watchlist Page)

| Test ID | Test Name | Steps | Success Criteria |
|---------|-----------|-------|------------------|
| D-01 | Open search modal | Navigate to `/watchlist`, click search icon | Search modal opens with input field |
| D-02 | Search movies | Type "Inception" in search, wait for results | Movie results appear with posters and titles |
| D-03 | Add movie to watchlist | Click "+" on "Inception" result | Movie added, appears in watchlist, toast confirmation |
| D-04 | Trending movies | Click "Trending" tab in modal | Shows TMDB trending movies |
| D-05 | Discover popular | Click "Discover" → "Popular" | Shows popular movies sorted by popularity |
| D-06 | Discover highly-rated | Click "Discover" → "Highly Rated" | Shows movies sorted by rating |
| D-07 | Movie detail card | Click on movie in watchlist | Full-screen detail modal opens with poster, rating, overview |
| D-08 | RT score display | View movie with RT data | Tomatometer score displayed if available |
| D-09 | Trailer link | View movie detail card | YouTube trailer button visible and functional |

### Suite 3: Swipe Voting (SwipeScreen)

| Test ID | Test Name | Steps | Success Criteria |
|---------|-----------|-------|------------------|
| S-01 | Swipe queue loads | As TestUser1, navigate to `/swipe` | Movie cards appear if watchlist has entries |
| S-02 | Swipe YES (right) | Drag card right past threshold | Card animates off-screen, YES vote recorded |
| S-03 | Swipe NO (left) | Drag card left past threshold | Card animates off-screen, NO vote recorded |
| S-04 | Button vote YES | Click checkmark button | Vote recorded, next card shown |
| S-05 | Button vote NO | Click X button | Vote recorded, next card shown |
| S-06 | Mark already watched | Click "Already Watched" button | Movie marked watched for this member, removed from queue |
| S-07 | Empty queue | Vote on all movies | "No more movies" message displayed |
| S-08 | Content filtering (Kids) | Log in as KidUser (Kids filter), go to `/swipe` | Only G/PG rated movies shown |
| S-09 | Different user queue | Switch to TestUser2, navigate to `/swipe` | Full queue shown (hasn't voted yet) |
| S-10 | Vote persistence | Vote on movie, refresh page, check queue | Previously voted movies not in queue (moved from X-04) |

### Suite 4: Cross-User Voting Scenarios

> **STATUS: CANCELLED** - Out of scope for current use case.
>
> **Rationale**: For simple home use, one user controls the device while discussing choices with others in the room. Cross-device independent voting functionality does not currently exist and isn't needed. The match algorithm and movie night flow work correctly with single-user operation on behalf of the group.
>
> These tests would be relevant if/when multi-device sync is implemented in the future.

| Test ID | Test Name | Status | Notes |
|---------|-----------|--------|-------|
| ~~X-01~~ | ~~Both users YES~~ | CANCELLED | Requires cross-device voting |
| ~~X-02~~ | ~~One YES one NO~~ | CANCELLED | Requires cross-device voting |
| ~~X-03~~ | ~~Partial voting~~ | CANCELLED | Requires cross-device voting |
| X-04 | Vote persistence | **MOVED to S-10** | Single-user functionality, still valid |

### Suite 5: Movie Night Flow

| Test ID | Test Name | Steps | Success Criteria |
|---------|-----------|-------|------------------|
| N-01 | Navigate to movie night | Click movie night icon in nav | `/movie-night` loads with member selection stage |
| N-02 | Select attendees | Check TestUser1 and TestUser2 checkboxes, click continue | Proceeds to match browsing stage |
| N-03 | View matches | On match browsing stage | Shows movies where all selected members voted YES |
| N-04 | Match sorting | View match list | Sorted by: YES count desc → non-voters watched asc → recency |
| N-05 | Pick movie | Swipe/select a matched movie | Proceeds to confirmation stage |
| N-06 | Mark watched | Select which members watched, confirm | MemberWatched records created, movie marked inactive |
| N-07 | Content filter applied | Include KidUser in attendees | Only shows matches within Kids content rating |
| N-08 | No matches message | Select members with no common YES votes | "No matches" message displayed |

### Suite 6: Watch History

| Test ID | Test Name | Steps | Success Criteria |
|---------|-----------|-------|------------------|
| H-01 | View history | As TestUser1, navigate to `/history` | Shows list of watched movies with dates |
| H-02 | Watch stats | Check stats section | Shows total watched count, genres breakdown |
| H-03 | Per-user history | Switch to TestUser2, view history | Shows different watch history |
| H-04 | Watched tab in watchlist | Go to `/watchlist`, click "Watched" tab | Shows inactive/watched movies |

### Suite 7: Watchlist Management

| Test ID | Test Name | Steps | Success Criteria |
|---------|-----------|-------|------------------|
| W-01 | Remove from watchlist | On movie detail, click remove button | Movie removed, no longer in list |
| W-02 | Add duplicate prevention | Try adding same movie twice | Error or no-op, no duplicate entry |
| W-03 | Watchlist source tracking | Add movie, check detail | Shows "Added by [member name]" |
| W-04 | Active vs inactive | Mark movie watched, check lists | Moves from active to watched/inactive |

### Suite 8: Navigation & UI

| Test ID | Test Name | Steps | Success Criteria |
|---------|-----------|-------|------------------|
| U-01 | Bottom nav | Click each nav icon | Navigates to correct page |
| U-02 | Help tooltip | Click "?" button | Context-sensitive help overlay appears |
| U-03 | Back navigation | Use browser back button | Correct previous page loaded |
| U-04 | Session persistence | Refresh page | Stays logged in as same member |
| U-05 | Logout/switch user | Go to `/`, click different member | Session switches, new member context |
| U-06 | Mobile responsive | Resize viewport to mobile size | UI adapts correctly, no overflow |

### Suite 9: Error Handling

| Test ID | Test Name | Steps | Success Criteria |
|---------|-----------|-------|------------------|
| E-01 | Network error recovery | Disconnect backend, try action, reconnect | Error message shown, retry works |
| E-02 | Invalid member | Navigate with invalid member ID in storage | Redirects to member select |
| E-03 | Empty states | New user with no watchlist | Appropriate empty state messages |

---

## Test Execution Order

**Phase 1: Setup & Member Tests** (M-01 through M-07)
- Establishes test members for scenarios

**Phase 2: Content Population** (D-01 through D-09)
- Adds movies to watchlist for voting tests

**Phase 3: Single-User Voting** (S-01 through S-10)
- Tests swipe mechanics, queue behavior, and vote persistence

**Phase 4: Cross-User Voting** ~~(X-01 through X-04)~~ - **CANCELLED**
- ~~Validates multi-user vote interactions~~
- Out of scope: Single-device home use assumed

**Phase 5: Movie Night Flow** (N-01 through N-08)
- Tests match calculation and watched marking

**Phase 6: History & Cleanup** (H-01 through H-04, W-01 through W-04)
- Validates history tracking and list management

**Phase 7: UI/UX** (U-01 through U-06, E-01 through E-03)
- Navigation, responsiveness, error handling

---

## Defect Tracking

When a test fails, document:
1. **Test ID** that failed
2. **Expected vs Actual** behavior
3. **Console errors** (use `read_console_messages`)
4. **Network requests** (use `read_network_requests`)
5. **DOM state** at failure point

Then dispatch fix agent with specific instructions.

---

## Success Metrics

- **Pass Rate**: All tests must pass
- **No Console Errors**: No uncaught exceptions during test run
- **Network Success**: All API calls return expected status codes
- **Visual Correctness**: UI matches expected state at each step
