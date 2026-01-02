# User Profile Nav Item Design

## Problem

Once a user selects their profile on the landing page, there's no persistent indicator of who's logged in. Family members may:
1. Forget which profile is active on a shared device
2. Want to quickly switch profiles without navigating back manually

## Solution

Add a 5th navigation item to the bottom nav showing the current user's avatar.

## Design Details

### Navigation Item
- **Position**: Far right of bottom nav (5th item)
- **Icon**: User's avatar (26x26px, circular)
- **Label**: "User"
- **Action**: Navigate to `/` (existing UserSelect page)

### Visual Behavior

**With custom avatar:**
- Display the user's uploaded avatar image
- Circular crop matching avatar style elsewhere in app

**Without custom avatar (initials fallback):**
- Colored circle background using existing `AVATAR_COLORS` palette
- 1-2 letter initials (first letters of name parts)
- Same logic as UserSelect page for consistency

**No user selected:**
- Generic person silhouette icon
- "User" label still shown
- Tapping navigates to UserSelect

### Active State
- No special active state needed
- UserSelect page (`/`) doesn't display the bottom nav, so this item will never appear "active"

## Data Flow

1. `BottomNav` component uses `useCurrentMember()` hook to get `memberId`
2. Fetches member data via TanStack Query (uses cached `['members']` query)
3. Renders avatar or initials based on member data
4. Falls back to silhouette if no member selected

## Implementation Notes

- Reuse `AVATAR_COLORS` array (import from UserSelect or extract to shared location)
- Reuse `getInitials()` logic from UserSelect
- Avatar image URL construction matches existing pattern in UserSelect
- No new API endpoints required
- No new pages required (reuses existing UserSelect)

## Files to Modify

1. `frontend/src/components/BottomNav.tsx` - Add user nav item with avatar logic
2. `frontend/src/components/BottomNav.css` - Style for avatar in nav

## Out of Scope

- Profile editing from nav (use existing long-press on UserSelect)
- Quick-switch popup (navigates to full UserSelect instead)
- Settings or preferences page
