# Movie Night Flow Simplification

## Problem

The current Movie Night flow has two redundant stages:
1. **"Your Matches"** - Shows matched movies in a list with "Start Runoff Vote" button
2. **"Cast Your Vote"** - Shows the same movies as clickable grid

The voting mechanism also doesn't work across devices (in-memory storage), and the multi-step process doesn't match how families actually decide on movies.

## Real-World Behavior

When families pick a movie from a shortlist, they typically:
1. Browse through the options
2. Watch trailers to remember what each movie is about
3. Discuss as a group
4. Pick one

## Solution

Replace `matches` and `voting` stages with a single **full-screen swipeable card browser**.

### New Flow

```
select → browse → winner → completion
```

| Stage | Description |
|-------|-------------|
| `select` | Pick who's watching (unchanged) |
| `browse` | Swipe through matched movies, watch trailers, tap "Watch This" to pick |
| `winner` | Celebration screen (unchanged) |
| `completion` | Mark who watched (unchanged) |

### Browse Stage UI

```
┌─────────────────────────────────┐
│  Pick a Movie        1 of 4  ○○○│  ← Header with position dots
├─────────────────────────────────┤
│                                 │
│         ┌─────────────┐         │
│         │             │         │
│         │   POSTER    │         │
│         │             │         │
│         │             │         │
│         └─────────────┘         │
│                                 │
│      Dune: Part Two (2024)      │
│         ★ 8.7  🍅 94%           │  ← RT scores if available
│                                 │
│    Epic continuation of the     │
│    saga of Paul Atreides...     │  ← Synopsis (truncated)
│                                 │
│      [ ▶ Watch Trailer ]        │  ← Opens trailer (YouTube)
│                                 │
│      [   Watch This   ]         │  ← Primary action → winner stage
│                                 │
│  ← swipe to browse →            │  ← Hint text (fade after first use)
└─────────────────────────────────┘
```

### Gestures & Interactions

| Action | Result |
|--------|--------|
| Swipe left | Next movie |
| Swipe right | Previous movie |
| Tap "Watch Trailer" | Opens trailer URL (YouTube) |
| Tap "Watch This" | Movie becomes winner → celebration screen |
| Position dots | Visual indicator of position in stack |

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| 0 matches | Show "No matches found" with suggestion to add more movies or change who's watching |
| 1 match | Skip browse, go straight to winner (current behavior preserved) |
| 2+ matches | Show browse cards |
| No trailer URL | Hide "Watch Trailer" button |
| No RT scores | Hide ratings line |

## Implementation Changes

### Frontend (`MovieNight.tsx`)

1. Remove `voting` stage from Stage type
2. Remove `sessionId`, `votedMovie` state
3. Remove `startVotingMutation`, `voteMutation`, `resultMutation`
4. Replace `matches` stage JSX with swipeable card carousel
5. Add position tracking state (`currentIndex`)
6. "Watch This" button sets result and goes to `winner` stage

### Frontend (`client.ts`)

1. Remove `startRunoff`, `castVote`, `getRunoffResult` functions (now unused)

### Backend (`movie_night.py`)

1. Remove `/start-runoff`, `/vote/{session_id}`, `/result/{session_id}` endpoints
2. Remove `active_votes` in-memory storage
3. Keep only `/matches` endpoint

### Styling (`MovieNight.css`)

1. Add card carousel styles
2. Add position indicator dots
3. Trailer button styling

## Migration

- No database changes required
- No breaking API changes for other clients (endpoints removed were only used by this screen)

## Testing

1. Verify 0 matches shows empty state
2. Verify 1 match skips to winner
3. Verify 2+ matches shows card browser
4. Verify swipe navigation works
5. Verify trailer opens correctly
6. Verify "Watch This" completes flow
7. Run existing tests (should still pass)
