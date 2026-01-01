# Family Flix Picker - Design Document

## Problem

Family movie night decisions take forever. Core pain points:
- **Veto wars** - someone always shoots down suggestions
- **Mood mismatch** - one wants comedy, another wants action
- **Seen-it syndrome** - keep suggesting movies someone already watched
- **The "meh" problem** - can't find anything that excites everyone

## Solution

An async swiping app where family members vote on movies independently throughout the week. When movie night arrives, the app reveals matches and a quick runoff picks the winner.

## Family Context

- Adults + teens (including Monty, 13)
- 2-7 registered family members (allows for partners/spouses of older kids)
- Quality-focused movie enthusiasts
- Mix of streaming services + rentals
- All have iPhones

---

## Core Flow

### 1. Add to Pool

Family members add movies to a shared pool from:
- **Personal watchlist** - search TMDB, tap to add
- **Bulk import** - paste messy lists, AI matches against TMDB
- **Curated lists** - subscribe to "best of" collections (genres, decades, awards)
- **Trending/new releases** - pulled automatically from TMDB

### 2. Swipe Anytime

- Open app when you have a spare moment
- See movie card: poster, title, year, synopsis, rating, content indicator
- Swipe right (yes) or left (no)
- Optional mood filter: "Show me comedies" or "Anything goes"
- Personal nudge if you have unswiped movies (only you see this)

### 3. Matches Accumulate

- Behind the scenes, app tracks overlapping "yes" votes
- A movie is a "match" when everyone present has swiped "yes"
- Swipes are private - no one sees your "no" votes

### 4. Movie Night Runoff

1. Someone taps "Movie Night!"
2. Select who's watching (tap family member avatars)
3. App calculates matches for those people only
4. Top 3-5 matches shown as cards
5. Everyone present votes for their favorite
6. Winner announced (tie = random from tied)

### 5. Mark Watched

- After the movie: "Did you watch [Movie]?"
- Mark as watched → removed from pool, added to history

---

## Match Calculation Logic

### Ranking matches:

1. **Source priority** - family watchlist beats curated list
2. **Recency** - newer additions surface first
3. **Vote count** - for partial matches if not enough full matches

### Edge cases:

- **No matches** → show "top contenders" with most yes votes, note who needs to swipe
- **Only 1 match** → skip voting, celebrate the unanimous choice
- **Someone hasn't swiped** → their vote treated as neutral (doesn't block matches)

---

## Content Filtering

- Movies tagged 16+ (Common Sense Media) or R18+ (Australian) hidden from Monty's swipe queue
- Adults still see these movies
- Such movies can match if all present adults agree (Monty excluded from calculation)

---

## User Interface

### Screens:

1. **Swipe Screen** (home)
   - Movie card with poster, title, year, synopsis
   - Swipe gestures or tap buttons
   - Mood filter toggle
   - Badge: "12 movies to swipe"

2. **Movie Night Screen**
   - "Who's watching?" avatar selection
   - "Start Movie Night" button
   - Runoff cards → vote → winner with fanfare

3. **Watchlist Screen**
   - All movies in pool
   - Filters: added by me, unswiped, matched
   - Add movie search
   - Bulk import (in menu)

4. **Watch History**
   - Simple list with dates
   - Stats: "47 movies watched in 2025"

5. **Settings**
   - Switch user
   - Content filters per member
   - Curated list subscriptions
   - Bulk import

### Design vibe:

- Dark mode default (movie night aesthetic)
- Poster-forward - big images, minimal text
- Playful but not childish

---

## Technical Architecture

### Deployment:

- Docker container on Proxmox mini-PC
- Accessed via local URL (e.g., `movies.local`)
- SQLite database (single file, easy backup to Synology)

### Tech stack:

- **Frontend:** React PWA - mobile-optimized swipe UI
- **Backend:** Python (FastAPI) - lightweight API server
- **Database:** SQLite
- **External API:** TMDB (free tier) for movie data, posters, ratings

### Data stored:

- Family members (name, content filter level)
- Movie pool (TMDB IDs + cached metadata)
- Swipe votes per person
- Watch history
- Watchlist contributions

### PWA setup:

- Each family member visits URL on iPhone
- "Add to Home Screen" - appears as app icon
- Launches fullscreen, feels native
- No app store required

---

## Authentication

Minimal - it's a private family network:

- First visit: "Who are you?" → tap your name
- Device remembers selection
- No passwords or emails
- Settings → "Switch User" if needed

---

## Bulk Import Feature

Power-user feature for seeding existing lists:

- Paste rough list (bullets, numbered, comma-separated, typos OK)
- AI parses and fuzzy-matches against TMDB
- Review screen: "Found 47/50 matches"
- Unmatched shown for manual correction
- One tap to add all confirmed matches

Access via Settings → "Import Watchlist"

---

## Summary

| Aspect | Decision |
|--------|----------|
| Core mechanic | Async swiping + movie night runoff |
| Family size | 2-7 members |
| Movie sources | Watchlist + curated lists + trending |
| Matching | Present members only, full consensus |
| Content filtering | 16+/R18+ hidden from Monty |
| Platform | Self-hosted PWA on Proxmox |
| Tech stack | React + FastAPI + SQLite + TMDB |
| Auth | Name picker, no passwords |
