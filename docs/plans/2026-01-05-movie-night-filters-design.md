# Movie Night Filters Design

## Overview

Add client-side filtering to the Movie Night browse stage, allowing users to narrow down matched movies using quick filters and genre selection.

## Location in Flow

```
Select Members → [Find Matches] → Browse Stage (FILTERS HERE) → Pick Winner → Mark Watched
```

## UI Layout

```
┌─────────────────────────────────┐
│  Pick a Movie       3 of 8 (12) │  ← Header with filtered/total count
├─────────────────────────────────┤
│  ═══════════●═══════════════    │  ← Progress bar (unchanged)
├─────────────────────────────────┤
│  [< 2hrs] [🍅 70%+] [no 18+] [New] │  ← Quick filter chips
│  [Action] [Comedy] [Sci-Fi] →   │  ← Genre chips (horizontal scroll)
├─────────────────────────────────┤
│                                 │
│         (Movie Card)            │
│                                 │
├─────────────────────────────────┤
│       ← swipe to browse →       │
└─────────────────────────────────┘
```

## Filter Specifications

### Quick Filters (Row 1)

| Chip Label | Logic | Notes |
|------------|-------|-------|
| `< 2hrs` | `movie.runtime < 120` | If runtime is null, movie is excluded when filter active |
| `🍅 70%+` | `movie.rt_critic_score >= 70` | If RT score is null, movie is excluded when filter active |
| `no 18+` | `movie.content_rating !== 'adult'` | Excludes only "adult" rating; "mature" still shown |
| `New` | `movie.year >= (currentYear - 1)` | For 2026, shows 2025-2026 releases |

### Genre Chips (Row 2)

- **Source:** Extract unique genres from current (unfiltered) match list
- **Display:** Sorted alphabetically, horizontal scroll if overflow
- **Multi-select:** Multiple genres can be active (OR logic between genres)
- **Dynamic:** Only shows genres present in current matches

### Combined Filter Logic

```
Quick filters: AND (all active quick filters must pass)
Genre filters: OR (any selected genre matches)
Combined: QuickFilters AND GenreFilters

Example: [< 2hrs] + [🍅 70%+] + [Action, Comedy]
→ (runtime < 120) AND (rt_score >= 70) AND (genre includes Action OR Comedy)
```

## Interaction Behavior

- Chips are toggles (tap to activate, tap again to deactivate)
- Multiple filters can be active simultaneously
- Active chips get highlighted styling (filled background)
- Header updates: "3 of 12" → "3 of 8 (12)" showing filtered vs total
- When filters change, `currentIndex` resets to 0
- Filters reset when leaving browse stage (no persistence needed)

## State Management

### New State

```typescript
const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());
const [selectedGenres, setSelectedGenres] = useState<Set<string>>(new Set());
```

### Derived Values

```typescript
// Extract unique genres from unfiltered matches
const availableGenres = useMemo(() => {
  const genres = new Set<string>();
  matches.forEach(m => {
    parseGenres(m.movie.genres).forEach(g => genres.add(g));
  });
  return Array.from(genres).sort();
}, [matches]);

// Apply filters to matches
const filteredMatches = useMemo(() => {
  return matches.filter(m => {
    const movie = m.movie;

    // Quick filters (AND)
    if (activeFilters.has('< 2hrs') && (movie.runtime == null || movie.runtime >= 120)) return false;
    if (activeFilters.has('🍅 70%+') && (movie.rt_critic_score == null || movie.rt_critic_score < 70)) return false;
    if (activeFilters.has('no 18+') && movie.content_rating === 'adult') return false;
    if (activeFilters.has('New') && (movie.year == null || movie.year < new Date().getFullYear() - 1)) return false;

    // Genre filters (OR)
    if (selectedGenres.size > 0) {
      const movieGenres = parseGenres(movie.genres);
      if (!movieGenres.some(g => selectedGenres.has(g))) return false;
    }

    return true;
  });
}, [matches, activeFilters, selectedGenres]);
```

## UI Components & Styling

### Chip States

| State | Background | Border | Text |
|-------|------------|--------|------|
| Inactive | transparent | 1px solid rgba(255,255,255,0.3) | white, opacity 0.7 |
| Active | accent color | none | white, full opacity |
| Pressed | slightly darker accent | none | white |

### Styling Specs

- **Chip size:** `padding: 6px 12px`, `border-radius: 16px`, `font-size: 13px`
- **Row gap:** `8px` between chips
- **Row spacing:** `8px` between quick filter row and genre row
- **Container:** `padding: 8px 16px`, between progress bar and card
- **Genre row:** `overflow-x: auto`, `white-space: nowrap`, hide scrollbar

### Empty State

When all movies filtered out:
```
┌─────────────────────────────┐
│   No movies match filters   │
│                             │
│      [Clear Filters]        │
└─────────────────────────────┘
```

## Card Layout Redesign

Adding filter rows (~70px) compresses vertical space. A card layout redesign is recommended:

### Current Layout (Vertical Stack)
```
┌─────────────────────────────┐
│         POSTER              │
│         (large)             │
├─────────────────────────────┤
│ Title (Year)                │
│ ✓ [avatars] Everyone!       │
│ PG-13 · 142 min · TMDB 7.2  │
│ [Action] [Sci-Fi]           │
│ Synopsis text...            │
├─────────────────────────────┤
│ [▶ Trailer] [More]          │
│ [    Watch This    ]        │
└─────────────────────────────┘
```

### Proposed Layout (Side-by-Side)
```
├───────────┬─────────────────┤
│           │ Title (Year)    │
│  POSTER   │ PG-13 · 142 min │
│  (left)   │ 🍅 85% · TMDB 7.2│
│           │ [▶] [ℹ]         │
│           ├─────────────────┤
│           │ ✓ [avatars]     │
├───────────┴─────────────────┤
│ Synopsis text...            │
│ [Action] [Sci-Fi]           │
├─────────────────────────────┤
│ [      Watch This      ]    │
└─────────────────────────────┘
```

**Key changes:**
- Poster left (40% width), metadata right
- Trailer/More become compact icon buttons
- Voter stack below poster/metadata block
- Genres move to bottom with synopsis

**Note:** Use frontend-design skill to finalize layout and ensure mobile touch targets.

## Edge Cases

| Case | Handling |
|------|----------|
| Movie with null runtime | Excluded by "< 2hrs", included otherwise |
| Movie with null RT score | Excluded by "🍅 70%+", included otherwise |
| Movie with null year | Excluded by "New", included otherwise |
| Movie with no genres | Excluded when any genre filter active |
| Only 1 match after filtering | Stay in browse stage; user can adjust filters or pick winner |
| 0 matches initially (before filtering) | No filter UI shown (existing empty state) |
| All matches are same genre | Genre row shows single chip |
| No adult movies in matches | "no 18+" chip still shown (no effect) |
| No genres in match set | Hide genre row entirely |

## Testing Scenarios

| Scenario | Expected Behavior |
|----------|-------------------|
| No filters active | All matches shown, chips unhighlighted |
| Single quick filter | Only matching movies shown, count updates |
| Multiple quick filters | AND logic applied, stricter filtering |
| Single genre selected | Only movies with that genre shown |
| Multiple genres selected | OR logic (movies with ANY selected genre) |
| Quick filter + genres | Combined: quick AND genre filters |
| All movies filtered out | Empty state with "Clear Filters" button |
| Clear filters | All chips deactivate, full list restored |
| Filter then swipe to end | Can't swipe past filtered list length |
| Change filters mid-browse | Index resets to 0, new filtered list shown |

## Implementation Notes

- All filtering is client-side (no API changes needed)
- Filter state is local to MovieNight component
- No persistence between sessions
- Consider extracting FilterChips as separate component if file gets large
