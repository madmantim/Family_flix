# Help Tooltip Design

## Overview

Add an on-demand help tooltip to explain UI action icons without cluttering the interface. Users tap a (?) icon in the header to see what each button means.

## Problem

The app uses icon-only buttons (✕, ♥, 👁, 🗑) whose meaning may not be immediately obvious to new users. Need a simple way to explain these without forced onboarding or persistent labels.

## Solution

Small (?) help icon in the header bar that shows a tooltip with icon explanations when tapped.

## Screens Affected

1. **SwipeScreen** - Primary screen where users first encounter action icons
2. **Watchlist** - Detail card has same icons plus remove

## Design Details

### Help Button Placement

**SwipeScreen header:**
```
[Switch User]     Member Name     (?)  X left
```

**Watchlist header:**
```
Watchlist              (?)   [Show Watched] [+ Add]
```

### Tooltip Content

**SwipeScreen:**
```
┌─────────────────────────────┐
│  ✕  Pass                    │
│  ♥  Watch / Rewatch         │
│  👁  Seen it                │
└─────────────────────────────┘
```

**Watchlist:**
```
┌─────────────────────────────┐
│  ✕  Pass                    │
│  ♥  Watch / Rewatch         │
│  👁  Seen it                │
│  🗑  Remove                 │
└─────────────────────────────┘
```

### Behavior

- Tap (?) → tooltip fades in (150-200ms)
- Tap anywhere outside → tooltip dismisses
- No close button needed

### Styling

**Help button (?):**
- 28px diameter circle
- Color: `rgba(255,255,255,0.5)` - muted, unobtrusive
- Subtle border matching existing UI
- Scale feedback on tap

**Tooltip:**
- Background: `rgba(0,0,0,0.9)`
- Border-radius: 8-12px
- Small arrow/notch pointing up toward (?)
- Each row: icon (left) + label (right-aligned text)
- Positioned below the (?) icon

## Implementation Approach

1. Create reusable `HelpTooltip` component
2. Add (?) button and tooltip to SwipeScreen header
3. Add (?) button and tooltip to Watchlist header
4. Style to match existing dark theme

## Out of Scope

- Forced first-time onboarding
- Help for MovieNight screen (different context)
- Persistent help or tutorials
