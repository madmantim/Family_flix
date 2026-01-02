# Watchlist Movie Detail Feature

## Overview

Add the ability to tap any movie in the watchlist grid to open a full-screen detail card. The card displays rich movie information (matching SwipeScreen layout) and provides actions to update preferences, toggle watched status, or remove from watchlist.

## UI Components

### MovieDetailCard (new component)

Reuses the visual layout from SwipeScreen's MovieCard:
- Full-screen poster background
- Movie metadata: title, year, runtime, TMDB score, RT score (linked), trailer link
- Genres as tags
- Overview/description text
- Watched toggle button (eye icon) in top-right of poster

### Action buttons at bottom

- Cross (NO) — left side, records NO swipe
- Heart (YES) — right side, records YES swipe
- Remove — center or secondary position, removes from watchlist

### Close mechanism

- Back button or tap-outside to dismiss without action
- Heart/Cross/Remove auto-close the card
- Watched toggle keeps card open

### Entry point

Tap any movie poster in the watchlist grid opens detail card with slide-up animation.

## Data Flow & API

### Opening the card

- Tap movie tile sets `selectedEntry: WatchlistEntry | null` state
- Card receives full Movie object from `WatchlistEntry.movie` (already loaded, no extra fetch needed)

### Actions and API calls

| Action | API Call | On Success |
|--------|----------|------------|
| Heart (YES) | `recordSwipe(memberId, movieId, 'yes', false)` | Close card, invalidate swipeQueue |
| Cross (NO) | `recordSwipe(memberId, movieId, 'no', false)` | Close card, invalidate swipeQueue |
| Watched Toggle | `markAsWatched(memberId, movieId)` | Stay open, update local state |
| Remove | `removeFromWatchlist(entryId)` | Close card, invalidate watchlist |

### Existing APIs used

- `recordSwipe` — already in client.ts, handles swipe recording
- `removeFromWatchlist` — already used by the X button on tiles
- `markAsWatched` — already in client.ts

No new backend endpoints needed — all functionality exists, just exposing it through a new UI.

### State to track

- `selectedEntry: WatchlistEntry | null` — which movie card is open
- Local watched state for the open card (reset when card closes)

## Component Structure

### File changes

```
frontend/src/
├── pages/
│   └── Watchlist.tsx        # Add selectedEntry state, render MovieDetailCard
├── components/
│   └── MovieDetailCard.tsx  # New component (extracted/adapted from SwipeScreen)
└── pages/
    └── Watchlist.css        # Add styles for detail card overlay
```

### MovieDetailCard props

```typescript
interface MovieDetailCardProps {
  entry: WatchlistEntry;
  memberId: number;
  onClose: () => void;
  onSwipe: (direction: SwipeDirection) => void;
  onRemove: () => void;
  onWatchedToggle: () => void;
  watched: boolean;
}
```

### Component reuse strategy

The MovieCard in SwipeScreen has drag logic baked in. Rather than refactor it, create a new MovieDetailCard that:
- Copies the visual layout (poster, metadata, genres, overview)
- Removes drag/swipe gesture handling
- Adds explicit button row with Heart, Cross, and Remove
- Wraps in a full-screen overlay with backdrop

This keeps SwipeScreen unchanged and avoids breaking existing functionality.

### Animation

- Use Framer Motion AnimatePresence
- Card slides up from bottom (initial: y: 100% to animate: y: 0)
- Backdrop fades in
- Exit reverses the animation

## Error Handling & Edge Cases

### API failures

- Heart/Cross swipe fails: Show brief toast/error, keep card open so user can retry
- Remove fails: Show error, keep card open
- Watched toggle fails: Revert local watched state, show error

### Edge cases

| Scenario | Behavior |
|----------|----------|
| Movie already swiped by user | Heart/Cross updates existing swipe (backend handles upsert) |
| Movie removed while card open | Card closes, grid refreshes (query invalidation handles this) |
| User taps backdrop | Close card without action |
| User taps close button | Close card without action |
| Watched toggle while pending | Disable button during mutation to prevent double-tap |

### Loading states

- While Heart/Cross/Remove mutation pending: disable all action buttons, show subtle spinner
- Prevent accidental double-taps

No offline handling — app assumes connectivity (consistent with existing behavior).

## Testing

### Manual testing checklist

- [ ] Tap movie tile opens full-screen detail card
- [ ] Card displays all metadata (title, year, runtime, scores, trailer, genres, overview)
- [ ] Heart button records YES swipe and closes card
- [ ] Cross button records NO swipe and closes card
- [ ] Watched toggle button toggles watched and stays open
- [ ] Remove button removes from watchlist and closes card
- [ ] Tap backdrop closes card without action
- [ ] Buttons disabled while mutation pending
- [ ] Card animates smoothly (slide up/down)
- [ ] Works on mobile viewport sizes

### Unit tests (optional, low priority)

- MovieDetailCard renders with correct props
- Action callbacks fire on button clicks

### Integration consideration

- Existing backend tests unaffected (no backend changes)
- Frontend is not currently unit tested; manual testing sufficient
