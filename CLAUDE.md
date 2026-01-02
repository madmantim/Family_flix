# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Family Flix Picker - A mobile-first PWA for async family movie voting. Family members swipe on movies (Tinder-style), and matches go to a shared watchlist for movie night runoffs.

## Commands

### Backend (from `backend/` directory)
```bash
# Activate virtualenv
source venv/bin/activate

# Run dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run single test file
pytest tests/test_matching.py

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

### Frontend (from `frontend/` directory)
```bash
# Dev server
npm run dev

# Build
npm run build

# Lint
npm run lint
```

### Docker
```bash
# From project root
docker-compose up --build
```

## Architecture

### Backend (Python FastAPI + SQLite)
- `app/main.py` - FastAPI app with CORS, includes all routers
- `app/models.py` - SQLAlchemy models: Member, Movie, Swipe, WatchlistEntry, WatchHistory, MemberWatched
- `app/routers/` - API endpoints split by domain:
  - `members.py` - CRUD for family members
  - `movies.py` - TMDB search/trending, movie metadata with RT scores and trailers
  - `swipes.py` - Swipe queue and vote recording
  - `watchlist.py` - Shared movie pool (movies all present members swiped YES on)
  - `movie_night.py` - Match calculation, runoff voting sessions
  - `history.py` - Watch history and stats
  - `watched.py` - Per-member watched status tracking
- `app/services/` - TMDB API integration

### Frontend (React + TypeScript + Vite)
- `src/App.tsx` - React Router setup with protected routes
- `src/pages/` - Five main screens:
  - `UserSelect` - Member picker at app start
  - `SwipeScreen` - Tinder-style swipe interface
  - `Watchlist` - Shared movie pool management
  - `MovieNight` - Match display and runoff voting
  - `History` - Watch history
- `src/api/client.ts` - Axios API client wrapping all backend endpoints
- `src/hooks/useCurrentMember.ts` - Session state for selected member
- `src/types/index.ts` - TypeScript interfaces matching backend schemas

### Data Flow
1. Member selects their profile at `/`
2. Swipe screen shows unwatched movies from watchlist that member hasn't swiped on
3. YES swipes from all present members → movie becomes a "match" for movie night
4. Movie night shows matches, optional runoff voting for ties
5. Watched movies tracked per-member with "would rewatch" flag

### External APIs
- TMDB for movie search, metadata, posters (credentials in `.env`)
- Rotten Tomatoes scores fetched via web scraping (stored in Movie model)
