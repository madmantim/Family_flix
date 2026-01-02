# Watchlist Movie Detail Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add ability to tap movies in watchlist grid to open full-screen detail card with swipe/watched/remove actions.

**Architecture:** New `MovieDetailCard` component renders as full-screen overlay. Watchlist tracks `selectedEntry` state. All actions use existing API functions — no backend changes.

**Tech Stack:** React, TypeScript, Framer Motion, TanStack Query

---

## Task 1: Create MovieDetailCard Component Shell

**Files:**
- Create: `frontend/src/components/MovieDetailCard.tsx`
- Create: `frontend/src/components/MovieDetailCard.css`

**Step 1: Create the component file with props interface**

```typescript
// frontend/src/components/MovieDetailCard.tsx
import { motion } from 'framer-motion';
import type { WatchlistEntry, SwipeDirection } from '../types';
import './MovieDetailCard.css';

interface MovieDetailCardProps {
  entry: WatchlistEntry;
  memberId: number;
  watched: boolean;
  isPending: boolean;
  onClose: () => void;
  onSwipe: (direction: SwipeDirection) => void;
  onRemove: () => void;
  onWatchedToggle: () => void;
}

export function MovieDetailCard({
  entry,
  memberId,
  watched,
  isPending,
  onClose,
  onSwipe,
  onRemove,
  onWatchedToggle,
}: MovieDetailCardProps) {
  const movie = entry.movie;

  const parseGenres = (genres: string | null): string[] => {
    if (!genres) return [];
    try {
      return JSON.parse(genres);
    } catch {
      return [];
    }
  };

  return (
    <motion.div
      className="movie-detail-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="movie-detail-card"
        initial={{ y: '100%' }}
        animate={{ y: 0 }}
        exit={{ y: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className="poster"
          style={{
            backgroundImage: movie.poster_url ? `url(${movie.poster_url})` : undefined,
          }}
        >
          {!movie.poster_url && <div className="no-poster">No Poster</div>}

          <button className="close-btn" onClick={onClose}>
            ✕
          </button>

          <button
            className={`watched-toggle ${watched ? 'active' : ''}`}
            onClick={onWatchedToggle}
            disabled={isPending}
          >
            👁
          </button>
        </div>

        <div className="info">
          <h2>{movie.title}</h2>
          <div className="meta">
            {movie.year && <span>{movie.year}</span>}
            {movie.runtime && <span>{movie.runtime} min</span>}
            {movie.vote_average && <span>TMDB {(movie.vote_average / 10).toFixed(1)}</span>}
            {movie.rt_critic_score && (
              movie.rt_url ? (
                <a
                  href={movie.rt_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="rt-score"
                >
                  🍅 {movie.rt_critic_score}%
                </a>
              ) : (
                <span className="rt-score">🍅 {movie.rt_critic_score}%</span>
              )
            )}
            {movie.trailer_url && (
              <a
                href={movie.trailer_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="trailer-link"
              >
                ▶ Trailer
              </a>
            )}
          </div>
          {movie.genres && (
            <div className="genres">
              {parseGenres(movie.genres).slice(0, 3).map((g) => (
                <span key={g} className="genre">{g}</span>
              ))}
            </div>
          )}
          <p className="overview">{movie.overview}</p>
        </div>

        <div className="action-row">
          <motion.button
            className="action-btn no"
            onClick={() => onSwipe('no')}
            disabled={isPending}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            ✕
          </motion.button>
          <motion.button
            className="action-btn remove"
            onClick={onRemove}
            disabled={isPending}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            🗑
          </motion.button>
          <motion.button
            className="action-btn yes"
            onClick={() => onSwipe('yes')}
            disabled={isPending}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            ♥
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
}
```

**Step 2: Create the CSS file**

```css
/* frontend/src/components/MovieDetailCard.css */
.movie-detail-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.movie-detail-card {
  width: 100%;
  max-width: 400px;
  max-height: 95vh;
  background: #1a1a2e;
  border-radius: 20px 20px 0 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.movie-detail-card .poster {
  position: relative;
  width: 100%;
  aspect-ratio: 2/3;
  max-height: 50vh;
  background-size: cover;
  background-position: center top;
  background-color: #2a2a3e;
  flex-shrink: 0;
}

.movie-detail-card .no-poster {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 1.2rem;
}

.movie-detail-card .close-btn {
  position: absolute;
  top: 0.75rem;
  left: 0.75rem;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
}

.movie-detail-card .watched-toggle {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.5);
  background: rgba(0, 0, 0, 0.5);
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  transition: all 0.2s ease;
}

.movie-detail-card .watched-toggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.movie-detail-card .watched-toggle.active {
  background: rgba(229, 9, 20, 0.9);
  border-color: #e50914;
  color: #fff;
}

.movie-detail-card .info {
  padding: 1rem;
  flex-shrink: 1;
  overflow: hidden;
}

.movie-detail-card h2 {
  margin: 0;
  font-size: 1.3rem;
  color: #fff;
  line-height: 1.2;
}

.movie-detail-card .meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.5rem;
  color: #888;
  font-size: 0.85rem;
}

.movie-detail-card .meta .rt-score {
  color: #fa320a;
  text-decoration: none;
}

.movie-detail-card .meta a.rt-score:hover {
  text-decoration: underline;
}

.movie-detail-card .meta .trailer-link {
  color: #ff0000;
  text-decoration: none;
  font-weight: 500;
}

.movie-detail-card .meta .trailer-link:hover {
  text-decoration: underline;
}

.movie-detail-card .genres {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}

.movie-detail-card .genre {
  padding: 0.2rem 0.6rem;
  background: rgba(229, 9, 20, 0.2);
  color: #e50914;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 500;
}

.movie-detail-card .overview {
  margin-top: 0.5rem;
  color: #aaa;
  font-size: 0.85rem;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.action-row {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2rem;
  padding: 1rem;
  padding-bottom: calc(env(safe-area-inset-bottom, 0) + 1rem);
  background: #1a1a2e;
}

.action-btn {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: none;
  font-size: 1.4rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.no {
  background: rgba(248, 113, 113, 0.2);
  color: #f87171;
}

.action-btn.yes {
  background: rgba(74, 222, 128, 0.2);
  color: #4ade80;
}

.action-btn.remove {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.1);
  color: #888;
  font-size: 1.2rem;
}
```

**Step 3: Verify files exist**

Run: `ls -la frontend/src/components/MovieDetailCard.*`

Expected: Both `.tsx` and `.css` files present

**Step 4: Commit**

```bash
git add frontend/src/components/MovieDetailCard.tsx frontend/src/components/MovieDetailCard.css
git commit -m "feat(watchlist): add MovieDetailCard component shell"
```

---

## Task 2: Integrate MovieDetailCard into Watchlist

**Files:**
- Modify: `frontend/src/pages/Watchlist.tsx`

**Step 1: Add imports at top of file**

Add after existing imports (around line 14):

```typescript
import { AnimatePresence } from 'framer-motion';
import { MovieDetailCard } from '../components/MovieDetailCard';
import { recordSwipe, markMovieWatched } from '../api/client';
import type { WatchlistEntry, SwipeDirection } from '../types';
```

Note: `AnimatePresence` is already imported, so just add `MovieDetailCard`, `recordSwipe`, `markMovieWatched`, and update the type import.

**Step 2: Add state for selected entry**

Add after the `showWatched` state (around line 25):

```typescript
const [selectedEntry, setSelectedEntry] = useState<WatchlistEntry | null>(null);
const [detailWatched, setDetailWatched] = useState(false);
```

**Step 3: Add mutations for swipe and watched**

Add after `removeMutation` (around line 62):

```typescript
const swipeMutation = useMutation({
  mutationFn: ({ movieId, direction }: { movieId: number; direction: SwipeDirection }) =>
    recordSwipe(memberId!, movieId, direction, false),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['swipeQueue'] });
    setSelectedEntry(null);
  },
});

const watchedMutation = useMutation({
  mutationFn: (movieId: number) => markMovieWatched(movieId, [memberId!], false),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['memberWatched', memberId] });
    setDetailWatched(true);
  },
});
```

**Step 4: Add click handler to movie poster**

Replace the movie-item div (around lines 148-175) to add onClick:

```typescript
{watchlist?.map((entry) => (
  <motion.div
    key={entry.id}
    className="movie-item"
    initial={{ opacity: 0, scale: 0.9 }}
    animate={{ opacity: 1, scale: 1 }}
    layout
  >
    <div
      className="poster"
      style={{
        backgroundImage: entry.movie.poster_url
          ? `url(${entry.movie.poster_url})`
          : undefined,
      }}
      onClick={() => {
        setSelectedEntry(entry);
        setDetailWatched(false);
      }}
    >
      {!entry.movie.poster_url && <span>No Poster</span>}
      <button
        className="remove-btn"
        onClick={(e) => {
          e.stopPropagation();
          removeMutation.mutate(entry.id);
        }}
      >
        ✕
      </button>
    </div>
    <div className="title">{entry.movie.title}</div>
    <div className="added-by">Added by {entry.added_by.name}</div>
  </motion.div>
))}
```

**Step 5: Add MovieDetailCard rendering**

Add before the closing `</div>` of watchlist-page (before bottom-nav, around line 243):

```typescript
<AnimatePresence>
  {selectedEntry && (
    <MovieDetailCard
      entry={selectedEntry}
      memberId={memberId}
      watched={detailWatched}
      isPending={swipeMutation.isPending || removeMutation.isPending || watchedMutation.isPending}
      onClose={() => setSelectedEntry(null)}
      onSwipe={(direction) => swipeMutation.mutate({ movieId: selectedEntry.movie.id, direction })}
      onRemove={() => {
        removeMutation.mutate(selectedEntry.id);
        setSelectedEntry(null);
      }}
      onWatchedToggle={() => {
        if (!detailWatched) {
          watchedMutation.mutate(selectedEntry.movie.id);
        }
      }}
    />
  )}
</AnimatePresence>
```

**Step 6: Verify no TypeScript errors**

Run: `cd frontend && npm run build`

Expected: Build succeeds with no errors

**Step 7: Commit**

```bash
git add frontend/src/pages/Watchlist.tsx
git commit -m "feat(watchlist): integrate MovieDetailCard with tap-to-open"
```

---

## Task 3: Add cursor pointer style for clickable posters

**Files:**
- Modify: `frontend/src/pages/Watchlist.css`

**Step 1: Add cursor pointer to movie poster**

Add after `.movie-item .poster` block (around line 99):

```css
.movie-item .poster {
  cursor: pointer;
}
```

Actually, modify the existing `.movie-item .poster` rule to add `cursor: pointer;`:

Find the block at lines 86-99 and add `cursor: pointer;` inside.

**Step 2: Commit**

```bash
git add frontend/src/pages/Watchlist.css
git commit -m "style(watchlist): add pointer cursor to movie posters"
```

---

## Task 4: Manual Testing

**Step 1: Start the dev servers**

Terminal 1:
```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2:
```bash
cd frontend && npm run dev
```

**Step 2: Test checklist**

Open browser to http://localhost:5173 and verify:

- [ ] Select a member at user select screen
- [ ] Navigate to Watchlist
- [ ] Tap a movie poster → detail card slides up from bottom
- [ ] Card shows: poster, title, year, runtime, scores, trailer link, genres, overview
- [ ] Tap backdrop (dark area) → card closes
- [ ] Tap close button (✕ top-left) → card closes
- [ ] Tap watched toggle (👁) → button becomes active (red), stays open
- [ ] Tap ♥ (YES) → card closes
- [ ] Tap ✕ (NO) → card closes
- [ ] Tap 🗑 (Remove) → card closes, movie removed from grid
- [ ] All buttons disabled while mutations pending (rapid tap protection)
- [ ] Card animates smoothly on open/close
- [ ] Works on mobile viewport (use browser dev tools)

**Step 3: Commit any fixes if needed**

---

## Task 5: Final Commit

**Step 1: Ensure all changes are committed**

Run: `git status`

Expected: Working tree clean

**Step 2: If any uncommitted changes, commit them**

```bash
git add -A
git commit -m "feat(watchlist): complete movie detail card feature"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Create MovieDetailCard component | `components/MovieDetailCard.tsx`, `components/MovieDetailCard.css` |
| 2 | Integrate into Watchlist | `pages/Watchlist.tsx` |
| 3 | Add pointer cursor style | `pages/Watchlist.css` |
| 4 | Manual testing | — |
| 5 | Final commit | — |

Estimated: 5 discrete commits, ~30 minutes implementation time.
