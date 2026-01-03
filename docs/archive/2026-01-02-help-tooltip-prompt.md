# Help Tooltip Implementation - Ralph Loop Prompt

## Quick Start

```bash
/ralph-loop "Implement docs/plans/2026-01-02-help-tooltip-impl.md" --max-iterations 10 --completion-promise "HELP TOOLTIP COMPLETE"
```

---

## Task

Implement the Help Tooltip feature following `docs/plans/2026-01-02-help-tooltip-impl.md`.

## Success Criteria

1. `frontend/src/components/HelpTooltip.tsx` exists and exports `HelpTooltip`
2. `frontend/src/components/HelpTooltip.css` exists with styling
3. SwipeScreen header shows (?) with 3-item tooltip (✕, ♥, 👁)
4. Watchlist header shows (?) with 4-item tooltip (✕, ♥, 👁, 🗑)
5. Tooltip opens on tap, closes on outside click
6. `npm run build` passes with no errors
7. All changes committed

## Workflow

Each iteration:
1. Read the implementation plan
2. Check current progress (which tasks done, which remain)
3. Execute next incomplete task step-by-step
4. Commit after each task
5. When all 4 tasks complete and build passes, output:

```
<promise>HELP TOOLTIP COMPLETE</promise>
```

## Files

- Plan: `docs/plans/2026-01-02-help-tooltip-impl.md`
- Create: `frontend/src/components/HelpTooltip.tsx`
- Create: `frontend/src/components/HelpTooltip.css`
- Modify: `frontend/src/pages/SwipeScreen.tsx`
- Modify: `frontend/src/pages/Watchlist.tsx`
