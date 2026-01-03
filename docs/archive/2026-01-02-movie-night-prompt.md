# Ralph Loop Prompt: Movie Night Simplification

## Context

Implement the design in `docs/plans/2026-01-02-movie-night-simplification.md`.

**Summary:** Replace redundant `matches` + `voting` stages with a single swipeable card browser.

## Checklist

Work through these items. Check the codebase to see what's already done.

### Backend Changes

- [ ] Remove from `backend/app/routers/movie_night.py`:
  - `active_votes` dict
  - `POST /start-runoff` endpoint
  - `POST /vote/{session_id}` endpoint
  - `POST /result/{session_id}` endpoint
- [ ] Remove from `backend/app/schemas.py`:
  - `VoteRequest` schema
  - `RunoffResult` schema

### Frontend Changes

- [ ] In `frontend/src/pages/MovieNight.tsx`:
  - Change Stage type to: `'select' | 'browse' | 'winner' | 'completion'`
  - Remove state: `sessionId`, `votedMovie`
  - Remove: `startVotingMutation`, `voteMutation`, `resultMutation`
  - Add state: `currentIndex` (number, default 0)
  - Replace `matches` stage with `browse` stage - swipeable cards using Framer Motion
  - Each card shows: poster, title, year, RT scores (if available), synopsis, trailer button (if available), "Watch This" button
  - Swipe gestures: drag left/right to navigate, threshold ~100px
  - Position dots at top
  - "Watch This" sets result and goes to `winner` stage

- [ ] In `frontend/src/api/client.ts`:
  - Remove: `startRunoff`, `castVote`, `getRunoffResult`

- [ ] In `frontend/src/types/index.ts`:
  - Remove: `RunoffResult` interface

- [ ] In `frontend/src/pages/MovieNight.css`:
  - Add browse card styles (full-screen, centered)
  - Add position dots styles
  - Add trailer button styles

### Edge Cases

- [ ] 0 matches: Show empty state message
- [ ] 1 match: Skip to winner (preserve existing behavior at line 39-46)
- [ ] No trailer_url: Hide trailer button
- [ ] No RT scores: Hide ratings

## Success Criteria

All must pass:

1. `cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest` - all tests pass
2. `cd /Users/tim/Claude/Movie_picker/frontend && npm run build` - builds without errors
3. No TypeScript errors
4. No unused imports or dead code from removed features

## Completion

When ALL checklist items are done AND all success criteria pass, output:

```
<promise>MOVIE NIGHT SIMPLIFIED</promise>
```

Do NOT output the promise until everything is complete and verified.
