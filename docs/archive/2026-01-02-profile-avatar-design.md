# Profile Avatar Upload Design

## Overview

Allow family members to set profile photos by long-pressing their avatar on the UserSelect screen. Photos are stored locally and auto-cropped to square.

## User Experience

1. User sees the UserSelect screen with member avatars
2. User long-presses (~500ms) on any avatar
3. Native file picker opens immediately (iOS shows photo library)
4. User selects an image
5. Image uploads to backend, auto-cropped to square
6. Avatar updates in place with the new image

**Visual feedback:**
- Loading spinner overlay on avatar during upload
- On success: avatar updates smoothly
- On error: alert with "Upload failed, try again"

## Backend

### New Endpoint

```
POST /api/members/{member_id}/avatar
Content-Type: multipart/form-data
Body: file (image)
Response: MemberResponse (updated member object)
```

### Processing Steps

1. Validate file is an image (JPEG, PNG, WebP)
2. Validate file size (<5MB)
3. Resize/crop to 256x256 square (center crop for non-square images)
4. Save to `backend/static/avatars/{member_id}.jpg`
5. Update `Member.avatar_url` to `/static/avatars/{member_id}.jpg`
6. Return updated member object

### Static File Serving

- Mount `/static` in FastAPI to serve `backend/static/`
- Avatars accessible at `http://localhost:8000/static/avatars/{member_id}.jpg`

### Dependencies

- `Pillow` for image processing (resize/crop)

## Frontend

### Changes to UserSelect.tsx

1. **Long-press detection:** `onTouchStart`/`onTouchEnd` with 500ms timer
2. **Hidden file input:** `<input type="file" accept="image/*">` triggered programmatically
3. **Upload state:** Track `uploadingMemberId` to show spinner on correct avatar

### New API Function

```typescript
// api/client.ts
export async function uploadAvatar(memberId: number, file: File): Promise<Member> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post(`/members/${memberId}/avatar`, formData);
  return response.data;
}
```

### Long-press Implementation

```tsx
const handleTouchStart = (memberId: number) => {
  timerRef.current = setTimeout(() => {
    setSelectedMemberId(memberId);
    fileInputRef.current?.click();
  }, 500);
};

const handleTouchEnd = () => {
  clearTimeout(timerRef.current);
};
```

## Error Handling

| Error | Handling |
|-------|----------|
| File too large (>5MB) | Reject with "Image too large" |
| Invalid file type | Reject with "Please select an image" |
| Network failure | Show "Upload failed, try again" |
| Backend processing error | Generic error message |

## File Structure

```
backend/
  static/
    avatars/
      1.jpg
      2.jpg
      ...
  app/
    routers/
      members.py  # Add avatar upload endpoint
```

## Testing

- Backend: pytest with test image fixtures, verify crop dimensions
- Frontend: manual testing on iOS device for photo picker behavior
- Integration: upload → verify static file exists → verify avatar displays
