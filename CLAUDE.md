# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Family Flix Picker** - A mobile-first PWA for async family movie voting. Family members swipe on movies (Tinder-style), and matches go to a shared watchlist for movie night selection.

**Key Features:**
- Tinder-style swipe voting on movies
- Shared family watchlist from TMDB search/discover
- Movie Night mode with smart match calculation
- Client-side filters (runtime, RT score, content rating, release year, genre)
- "Just Us" filter to show only movies absent members haven't voted YES on
- Per-member watch history and stats
- Content rating filtering (all_ages, teen, mature, adult)

**Tech Stack:**
- Backend: Python 3.11 + FastAPI + SQLAlchemy + SQLite
- Frontend: React 19 + TypeScript + Vite + TanStack Query + Framer Motion
- Deployment: Docker Compose with Nginx reverse proxy (currently on homelab via Tailscale)

## Commands

### Backend (from `backend/` directory)
```bash
source venv/bin/activate        # Activate virtualenv
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # Dev server
pytest                          # Run tests
pytest tests/test_matching.py   # Single test file
pytest --cov=app --cov-report=term-missing  # With coverage
```

### Frontend (from `frontend/` directory)
```bash
npm run dev      # Dev server (proxies /api to localhost:8000)
npm run build    # Production build
npm run lint     # ESLint check
```

### Docker
```bash
docker-compose up --build  # From project root (dev/local)
```

### Deployment
```bash
cd deploy && ./deploy.sh         # Deploy to homelab
./deploy.sh --first-run          # First-time deployment
```

## Architecture

### Backend Structure

**Main App (`app/main.py`):**
- FastAPI with CORS middleware
- Static file serving at `/static` for avatars
- Database initialization at startup
- Health check endpoint at `/api/health`

**Models (`app/models.py`):**
| Model | Purpose |
|-------|---------|
| Member | Family member profile (name, avatar_url, content_filter) |
| Movie | Cached movie metadata from TMDB with RT scores and trailer URL |
| WatchlistEntry | Shared pool entry (movie, added_by, source, is_active) |
| Swipe | Individual YES/NO vote on a movie |
| MemberWatched | Per-member watch history with timestamp |

**Routers (`app/routers/`):**

| Router | Endpoints | Purpose |
|--------|-----------|---------|
| members | `/api/members` | CRUD + avatar upload (resize/crop to 256x256) |
| movies | `/api/movies` | TMDB search, discover (popular/highly-rated) |
| swipes | `/api/swipes` | Vote recording, swipe queue (filtered by content rating) |
| watchlist | `/api/watchlist` | Add/remove movies, auto-fetches RT scores + trailers |
| movie_night | `/api/movie-night` | Match calculation with content filtering + absent voter tracking |
| watched | `/api/watched` | Watch history and stats per member |

**Services (`app/services/`):**
- `tmdb.py` - TMDB API integration (search, discover, trailers)
- `omdb.py` - OMDb API for Rotten Tomatoes critic scores

### Frontend Structure

**Pages (`src/pages/`):**
| Page | Route | Purpose |
|------|-------|---------|
| UserSelect | `/` | Member picker with avatar upload (long-press to edit) |
| SwipeScreen | `/swipe` | Tinder-style card swiping with drag gestures |
| Watchlist | `/watchlist` | Movie pool + search/discover modals + watched tab |
| MovieNight | `/movie-night` | 4-stage flow with filters: select → browse → pick → mark watched |
| History | `/history` | Personal watch stats and history list |

**Components (`src/components/`):**
- `BottomNav.tsx` - Bottom navigation bar with route highlighting
- `HelpTooltip.tsx` - Context-sensitive help overlay (? button)
- `MovieDetailCard.tsx` - Full-screen movie detail modal with swipe/remove actions

**API Client (`src/api/client.ts`):**
All backend endpoints wrapped with axios. Key functions:
- `searchMovies()`, `discoverMovies()` - TMDB movie discovery
- `getSwipeQueue()`, `recordSwipe()`, `getMemberSwipes()` - Voting
- `getWatchlist()`, `addToWatchlist()`, `removeFromWatchlist()` - Pool management
- `getMatches()` - Movie night match calculation
- `markMovieWatched()`, `getWatchHistory()`, `getWatchStats()` - Watch tracking

**Hooks (`src/hooks/`):**
- `useCurrentMember.ts` - Session state via localStorage

**Types (`src/types/index.ts`):**
TypeScript interfaces matching backend schemas:
- `Member`, `Movie`, `Swipe`, `WatchlistEntry`, `MemberWatched`
- `MatchedMovie` (includes `voters` and `absent_yes_voters` arrays)
- `MovieNightResponse`, `SwipeQueue`, `TMDBSearchResponse`, `WatchStats`

### Data Flow

1. **Member Selection** - Pick profile at `/`, stored in localStorage
2. **Swipe Queue** - Shows unwatched movies member hasn't voted on (content-filtered)
3. **Voting** - YES/NO swipes recorded, can mark as "already watched"
4. **Movie Night** - Select present members → browse matches with filters → pick winner
5. **Mark Watched** - Select who watched, updates per-member history

### Match Algorithm

1. Filter by most restrictive content rating among present members
2. For each active watchlist movie:
   - Count YES votes from present members
   - Track which absent members also voted YES (`absent_yes_voters`)
   - Count N(W) = members who didn't vote YES but have watched the movie
3. Sort by: YES count (descending) → N(W) count (ascending) → recency (newest first)

**Client-side Filters (Movie Night browse stage):**
- `< 2hrs` - Runtime under 120 minutes
- `🍅 70%+` - Rotten Tomatoes critic score >= 70
- `no 18+` - Excludes adult-rated content
- `New` - Released current or previous year
- `Just Us` - Only movies where no absent member voted YES
- Genre chips - OR logic for selected genres

### External APIs

| API | Purpose | Auth |
|-----|---------|------|
| TMDB | Movie search, metadata, posters, trailers | Bearer token (TMDB_ACCESS_TOKEN) |
| OMDb | Rotten Tomatoes critic score | API key (OMDB_API_KEY) |

**Environment Variables:**
```
TMDB_API_KEY=...
TMDB_ACCESS_TOKEN=...
OMDB_API_KEY=...
DATABASE_URL=sqlite:///./family_flix.db
```

## Testing

Backend tests in `backend/tests/`:
- `test_members.py` - Member CRUD
- `test_movies.py` - Movie endpoints
- `test_swipes.py` - Vote recording, queue filtering
- `test_matching.py` - Match calculation and sorting logic
- `test_member_watched.py` - Watch history, stats
- `test_ratings_and_trailers.py` - TMDB/OMDb integration
- `test_discover.py` - Discover endpoint
- `test_avatar.py` - Image upload/processing
- `test_watchlist.py` - Watchlist operations

## Project Documentation

- `CLAUDE.md` - This file (project guidance for Claude Code)
- `deploy/README.md` - Homelab deployment guide (Tailscale + Docker)
- `docs/archive/` - Completed feature designs and implementation docs

## Deployment

Current deployment is to homelab via Tailscale:
- **URL:** `http://mediastack-as.bone-egret.ts.net:8088`
- **Location:** Arthur's Seat homelab, LXC container 103
- **Access:** Requires Tailscale connection to bone-egret tailnet

See `deploy/README.md` for full deployment instructions including backup/restore procedures.
