# Family Flix Picker - Full Implementation

Build the Family Flix Picker app as specified in `docs/plans/2026-01-01-family-flix-picker-design.md`.

## Development Approach

1. **Check progress** - Review existing files, git log, and tests to understand current state
2. **Identify next task** - Pick the highest-priority unfinished work
3. **Implement with tests** - Write tests alongside each feature (pytest for backend, React Testing Library for frontend)
4. **Commit frequently** - Small, logical commits with descriptive messages
5. **Iterate until complete** - Continue through all features

## Tech Stack (per design doc)
- Frontend: React PWA with TypeScript, Vite, mobile-first
- Backend: Python FastAPI
- Database: SQLite with migrations
- External: TMDB API for movie data

## Configuration (ALREADY DONE)
- **TMDB API credentials** - Available in `.env` (both API key and access token)
- No user input required - proceed without pausing

## Frontend Requirements (CRITICAL)
Use the frontend-design skill principles:
- **Dark mode default** - movie night aesthetic with rich blacks and cinematic feel
- **Poster-forward** - large movie posters, minimal text
- **iPhone-optimized** - 390px width target, safe areas, touch-friendly (44px+ tap targets)
- **Bold typography** - distinctive fonts (avoid Inter/Roboto/Arial)
- **Smooth animations** - swipe gestures, card transitions, winner reveal fanfare
- **PWA manifest** - installable with app icon

## Testing Requirements
- Backend: pytest with >80% coverage on core logic (matching algorithm, vote counting)
- Frontend: Component tests for key interactions (swipe, vote, user selection)
- E2E: At least one happy-path test (swipe → match → movie night → winner)

## Implementation Order
1. Project scaffolding (Vite React + FastAPI + SQLite)
2. Database schema and migrations
3. TMDB integration (search, metadata, posters)
4. Backend API (members, movies, swipes, matches, watch history)
5. Frontend: User selection screen
6. Frontend: Swipe screen with gesture support
7. Frontend: Watchlist/pool management
8. Frontend: Movie Night runoff flow
9. Frontend: Watch history
10. PWA configuration (manifest, service worker, icons)
11. Docker deployment setup
12. Final testing and polish

## Completion Signal
When ALL of the following are true:
- All 5 screens functional (Swipe, Movie Night, Watchlist, History, Settings)
- Backend API complete with tests passing
- Frontend tests passing
- Docker Compose runs successfully
- PWA installable on iPhone

Output: <promise>FAMILY FLIX PICKER COMPLETE</promise>

---
Continue from current state. Check what exists, identify gaps, implement next priority.
