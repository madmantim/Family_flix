# Help Tooltip Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add on-demand (?) help icon to SwipeScreen and Watchlist headers that shows tooltip explaining action icons.

**Architecture:** Create reusable HelpTooltip component with configurable items. Add to both screen headers. Use React state for open/close, CSS for positioning and styling.

**Tech Stack:** React, TypeScript, CSS, Framer Motion (for animations)

---

### Task 1: Create HelpTooltip Component

**Files:**
- Create: `frontend/src/components/HelpTooltip.tsx`
- Create: `frontend/src/components/HelpTooltip.css`

**Step 1: Create component file with types and basic structure**

Create `frontend/src/components/HelpTooltip.tsx`:

```tsx
import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './HelpTooltip.css';

interface HelpItem {
  icon: string;
  label: string;
}

interface HelpTooltipProps {
  items: HelpItem[];
}

export function HelpTooltip({ items }: HelpTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (tooltipRef.current && !tooltipRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  return (
    <div className="help-tooltip-container" ref={tooltipRef}>
      <button
        className="help-btn"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Help"
      >
        ?
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="help-tooltip"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
          >
            <div className="tooltip-arrow" />
            {items.map((item, i) => (
              <div key={i} className="help-item">
                <span className="help-icon">{item.icon}</span>
                <span className="help-label">{item.label}</span>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
```

**Step 2: Create CSS file**

Create `frontend/src/components/HelpTooltip.css`:

```css
.help-tooltip-container {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.help-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.help-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.8);
}

.help-btn:active {
  transform: scale(0.95);
}

.help-tooltip {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: rgba(0, 0, 0, 0.92);
  border-radius: 10px;
  padding: 0.75rem 1rem;
  min-width: 160px;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.tooltip-arrow {
  position: absolute;
  top: -6px;
  right: 10px;
  width: 12px;
  height: 12px;
  background: rgba(0, 0, 0, 0.92);
  transform: rotate(45deg);
  border-radius: 2px;
}

.help-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.35rem 0;
  color: #fff;
  font-size: 0.9rem;
}

.help-item:not(:last-child) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.help-icon {
  font-size: 1.1rem;
  width: 24px;
  text-align: center;
}

.help-label {
  color: rgba(255, 255, 255, 0.85);
}
```

**Step 3: Verify build passes**

Run: `cd frontend && npm run build`
Expected: Build succeeds (component not yet used)

**Step 4: Commit**

```bash
git add frontend/src/components/HelpTooltip.tsx frontend/src/components/HelpTooltip.css
git commit -m "feat: add HelpTooltip component

Reusable tooltip component with configurable icon/label items.
Shows on tap, dismisses on outside click."
```

---

### Task 2: Add HelpTooltip to SwipeScreen

**Files:**
- Modify: `frontend/src/pages/SwipeScreen.tsx:229-235`
- Modify: `frontend/src/pages/SwipeScreen.css` (header styles if needed)

**Step 1: Import HelpTooltip**

Add import at top of `frontend/src/pages/SwipeScreen.tsx`:

```tsx
import { HelpTooltip } from '../components/HelpTooltip';
```

**Step 2: Define help items constant**

Add before the component function (around line 14):

```tsx
const SWIPE_HELP_ITEMS = [
  { icon: '✕', label: 'Pass' },
  { icon: '♥', label: 'Watch / Rewatch' },
  { icon: '👁', label: 'Seen it' },
];
```

**Step 3: Add HelpTooltip to header**

Modify the header section (around line 229-235). Change from:

```tsx
<header>
  <button className="back" onClick={handleSwitchUser}>
    Switch User
  </button>
  <span className="member-name">{member?.name}</span>
  <span className="count">{trueRemaining} left</span>
</header>
```

To:

```tsx
<header>
  <button className="back" onClick={handleSwitchUser}>
    Switch User
  </button>
  <span className="member-name">{member?.name}</span>
  <HelpTooltip items={SWIPE_HELP_ITEMS} />
  <span className="count">{trueRemaining} left</span>
</header>
```

**Step 4: Verify build passes**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 5: Manual test**

Run: `cd frontend && npm run dev`
- Navigate to SwipeScreen
- Verify (?) appears in header between name and count
- Tap (?) - tooltip should appear with 3 items
- Tap outside - tooltip should dismiss

**Step 6: Commit**

```bash
git add frontend/src/pages/SwipeScreen.tsx
git commit -m "feat: add help tooltip to SwipeScreen header

Shows (?) icon that explains ✕, ♥, 👁 actions."
```

---

### Task 3: Add HelpTooltip to Watchlist

**Files:**
- Modify: `frontend/src/pages/Watchlist.tsx:121-138`
- Modify: `frontend/src/pages/Watchlist.css` (header styles if needed)

**Step 1: Import HelpTooltip**

Add import at top of `frontend/src/pages/Watchlist.tsx`:

```tsx
import { HelpTooltip } from '../components/HelpTooltip';
```

**Step 2: Define help items constant**

Add before the component function:

```tsx
const WATCHLIST_HELP_ITEMS = [
  { icon: '✕', label: 'Pass' },
  { icon: '♥', label: 'Watch / Rewatch' },
  { icon: '👁', label: 'Seen it' },
  { icon: '🗑', label: 'Remove' },
];
```

**Step 3: Add HelpTooltip to header**

Modify the header section (around line 121-138). Change from:

```tsx
<header>
  <h1>{showWatched ? 'Watched' : 'Watchlist'}</h1>
  <div className="header-controls">
    <label className="show-watched-toggle">
      <span>Show Watched</span>
      <input
        type="checkbox"
        checked={showWatched}
        onChange={(e) => setShowWatched(e.target.checked)}
      />
    </label>
    {!showWatched && (
      <button className="add-btn" onClick={() => setShowSearch(true)}>
        + Add
      </button>
    )}
  </div>
</header>
```

To:

```tsx
<header>
  <h1>{showWatched ? 'Watched' : 'Watchlist'}</h1>
  <div className="header-controls">
    <HelpTooltip items={WATCHLIST_HELP_ITEMS} />
    <label className="show-watched-toggle">
      <span>Show Watched</span>
      <input
        type="checkbox"
        checked={showWatched}
        onChange={(e) => setShowWatched(e.target.checked)}
      />
    </label>
    {!showWatched && (
      <button className="add-btn" onClick={() => setShowSearch(true)}>
        + Add
      </button>
    )}
  </div>
</header>
```

**Step 4: Verify build passes**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 5: Manual test**

Run: `cd frontend && npm run dev`
- Navigate to Watchlist
- Verify (?) appears in header before the toggle
- Tap (?) - tooltip should appear with 4 items (includes 🗑)
- Tap outside - tooltip should dismiss

**Step 6: Commit**

```bash
git add frontend/src/pages/Watchlist.tsx
git commit -m "feat: add help tooltip to Watchlist header

Shows (?) icon that explains ✕, ♥, 👁, 🗑 actions."
```

---

### Task 4: Final Verification and Cleanup

**Step 1: Run full build**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no warnings

**Step 2: Run linter**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 3: Full manual test**

- SwipeScreen: (?) shows 3-item tooltip
- Watchlist: (?) shows 4-item tooltip
- Both: tooltip dismisses on outside click
- Both: tooltip positioning looks correct on mobile viewport

**Step 4: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: help tooltip adjustments"
```
