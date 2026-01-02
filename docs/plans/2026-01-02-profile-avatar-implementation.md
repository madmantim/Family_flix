# Profile Avatar Upload Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow members to set profile photos via long-press on UserSelect screen, with images stored locally and auto-cropped to 256x256.

**Architecture:** Backend receives multipart uploads, processes with Pillow (center-crop to square, resize to 256x256 JPEG), saves to static directory, updates member's avatar_url. Frontend triggers file picker on long-press, uploads to new endpoint, refreshes member list.

**Tech Stack:** Pillow (image processing), FastAPI static files, native HTML file input

---

## Task 1: Add Pillow Dependency

**Files:**
- Modify: `backend/requirements.txt:12`

**Step 1: Add Pillow to requirements**

Add this line to `backend/requirements.txt`:
```
Pillow>=10.0.0
```

**Step 2: Install dependency**

Run: `cd /Users/tim/Claude/Movie_picker/backend && pip install Pillow>=10.0.0`
Expected: Successfully installed Pillow

**Step 3: Verify installation**

Run: `python -c "from PIL import Image; print('Pillow OK')"`
Expected: `Pillow OK`

**Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add Pillow dependency for avatar image processing"
```

---

## Task 2: Create Static Directory and Mount in FastAPI

**Files:**
- Create: `backend/static/avatars/.gitkeep`
- Modify: `backend/app/main.py:1-10`

**Step 1: Create static directory structure**

Run: `mkdir -p /Users/tim/Claude/Movie_picker/backend/static/avatars && touch /Users/tim/Claude/Movie_picker/backend/static/avatars/.gitkeep`

**Step 2: Add static file mounting to main.py**

Add import at top of `backend/app/main.py`:
```python
from fastapi.staticfiles import StaticFiles
import os
```

Add after CORS middleware (around line 23):
```python
# Serve static files (avatars, etc.)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(os.path.join(static_dir, "avatars"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
```

**Step 3: Verify static mounting works**

Run: `cd /Users/tim/Claude/Movie_picker/backend && python -c "from app.main import app; print('Static mount OK')"`
Expected: `Static mount OK`

**Step 4: Run existing tests to ensure no breakage**

Run: `cd /Users/tim/Claude/Movie_picker/backend && pytest tests/test_members.py -v`
Expected: All tests pass

**Step 5: Commit**

```bash
git add backend/static/avatars/.gitkeep backend/app/main.py
git commit -m "feat: add static file serving for avatars"
```

---

## Task 3: Write Avatar Upload Endpoint Tests

**Files:**
- Create: `backend/tests/test_avatar.py`

**Step 1: Create test file with avatar upload tests**

Create `backend/tests/test_avatar.py`:
```python
import pytest
from io import BytesIO
from PIL import Image


def create_test_image(width=400, height=300, format="PNG"):
    """Create a test image in memory"""
    img = Image.new("RGB", (width, height), color="red")
    buffer = BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return buffer


def test_upload_avatar_success(client):
    # Create member first
    member_resp = client.post("/api/members/", json={"name": "Tim"})
    member_id = member_resp.json()["id"]

    # Upload avatar
    image = create_test_image(400, 300)
    response = client.post(
        f"/api/members/{member_id}/avatar",
        files={"file": ("test.png", image, "image/png")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"] is not None
    assert f"/static/avatars/{member_id}.jpg" in data["avatar_url"]


def test_upload_avatar_member_not_found(client):
    image = create_test_image()
    response = client.post(
        "/api/members/999/avatar",
        files={"file": ("test.png", image, "image/png")}
    )
    assert response.status_code == 404


def test_upload_avatar_invalid_file_type(client):
    # Create member first
    member_resp = client.post("/api/members/", json={"name": "Tim"})
    member_id = member_resp.json()["id"]

    # Try uploading a text file
    response = client.post(
        f"/api/members/{member_id}/avatar",
        files={"file": ("test.txt", BytesIO(b"not an image"), "text/plain")}
    )

    assert response.status_code == 400
    assert "image" in response.json()["detail"].lower()


def test_upload_avatar_overwrites_existing(client):
    # Create member
    member_resp = client.post("/api/members/", json={"name": "Tim"})
    member_id = member_resp.json()["id"]

    # Upload first avatar
    image1 = create_test_image(400, 300)
    client.post(
        f"/api/members/{member_id}/avatar",
        files={"file": ("test1.png", image1, "image/png")}
    )

    # Upload second avatar (should overwrite)
    image2 = create_test_image(500, 500)
    response = client.post(
        f"/api/members/{member_id}/avatar",
        files={"file": ("test2.png", image2, "image/png")}
    )

    assert response.status_code == 200
    # URL should be the same (overwritten file)
    assert f"/static/avatars/{member_id}.jpg" in response.json()["avatar_url"]
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/tim/Claude/Movie_picker/backend && pytest tests/test_avatar.py -v`
Expected: FAIL (endpoint doesn't exist yet)

**Step 3: Commit test file**

```bash
git add backend/tests/test_avatar.py
git commit -m "test: add avatar upload endpoint tests"
```

---

## Task 4: Implement Avatar Upload Endpoint

**Files:**
- Modify: `backend/app/routers/members.py`

**Step 1: Add imports to members.py**

Add these imports at the top of `backend/app/routers/members.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from PIL import Image
import os
from io import BytesIO
```

**Step 2: Add avatar upload endpoint**

Add this endpoint at the end of `backend/app/routers/members.py`:
```python
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
AVATAR_SIZE = 256
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/{member_id}/avatar", response_model=MemberResponse)
async def upload_avatar(
    member_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and set a member's avatar image"""
    # Validate member exists
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a JPEG, PNG, or WebP image."
        )

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 5MB.")

    # Process image with Pillow
    try:
        img = Image.open(BytesIO(content))
        img = img.convert("RGB")  # Ensure RGB for JPEG output

        # Center crop to square
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        img = img.crop((left, top, left + min_dim, top + min_dim))

        # Resize to target size
        img = img.resize((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)

        # Save to static directory
        static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static", "avatars")
        os.makedirs(static_dir, exist_ok=True)
        avatar_path = os.path.join(static_dir, f"{member_id}.jpg")
        img.save(avatar_path, "JPEG", quality=85)

    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to process image.")

    # Update member's avatar_url
    member.avatar_url = f"/static/avatars/{member_id}.jpg"
    db.commit()
    db.refresh(member)

    return member
```

**Step 3: Run avatar tests**

Run: `cd /Users/tim/Claude/Movie_picker/backend && pytest tests/test_avatar.py -v`
Expected: All 4 tests pass

**Step 4: Run all backend tests**

Run: `cd /Users/tim/Claude/Movie_picker/backend && pytest -v`
Expected: All tests pass

**Step 5: Commit**

```bash
git add backend/app/routers/members.py
git commit -m "feat: add avatar upload endpoint with image processing"
```

---

## Task 5: Add Frontend API Function

**Files:**
- Modify: `frontend/src/api/client.ts:30`

**Step 1: Add uploadAvatar function**

Add this function after `deleteMember` in `frontend/src/api/client.ts`:
```typescript
export const uploadAvatar = async (memberId: number, file: File): Promise<Member> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post<Member>(`/members/${memberId}/avatar`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};
```

**Step 2: Verify frontend builds**

Run: `cd /Users/tim/Claude/Movie_picker/frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "feat: add uploadAvatar API function"
```

---

## Task 6: Add Long-Press Handler and Upload UI to UserSelect

**Files:**
- Modify: `frontend/src/pages/UserSelect.tsx`
- Modify: `frontend/src/pages/UserSelect.css`

**Step 1: Update UserSelect.tsx imports**

Replace imports at top of `frontend/src/pages/UserSelect.tsx`:
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getMembers, createMember, uploadAvatar } from '../api/client';
import { useCurrentMember } from '../hooks/useCurrentMember';
import type { Member } from '../types';
import './UserSelect.css';
```

**Step 2: Add state and refs for long-press and upload**

Add after the existing state declarations (around line 17):
```typescript
const [uploadingId, setUploadingId] = useState<number | null>(null);
const longPressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
const fileInputRef = useRef<HTMLInputElement>(null);
const selectedMemberRef = useRef<number | null>(null);
```

**Step 3: Add upload mutation**

Add after `addMutation` (around line 31):
```typescript
const uploadMutation = useMutation({
  mutationFn: ({ memberId, file }: { memberId: number; file: File }) =>
    uploadAvatar(memberId, file),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['members'] });
    setUploadingId(null);
  },
  onError: () => {
    alert('Failed to upload avatar. Please try again.');
    setUploadingId(null);
  },
});
```

**Step 4: Add long-press handlers**

Add after existing handlers (around line 43):
```typescript
const handleTouchStart = (memberId: number) => {
  longPressTimer.current = setTimeout(() => {
    selectedMemberRef.current = memberId;
    fileInputRef.current?.click();
  }, 500);
};

const handleTouchEnd = () => {
  if (longPressTimer.current) {
    clearTimeout(longPressTimer.current);
    longPressTimer.current = null;
  }
};

const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  const memberId = selectedMemberRef.current;
  if (file && memberId) {
    setUploadingId(memberId);
    uploadMutation.mutate({ memberId, file });
  }
  // Reset input so same file can be selected again
  e.target.value = '';
};
```

**Step 5: Update the member-card button with touch handlers**

Replace the member-card motion.button (lines 68-90) with:
```tsx
<motion.button
  key={member.id}
  className="member-card"
  onClick={() => handleSelect(member)}
  onTouchStart={() => handleTouchStart(member.id)}
  onTouchEnd={handleTouchEnd}
  onMouseDown={() => handleTouchStart(member.id)}
  onMouseUp={handleTouchEnd}
  onMouseLeave={handleTouchEnd}
  initial={{ opacity: 0, scale: 0.8 }}
  animate={{ opacity: 1, scale: 1 }}
  transition={{ delay: index * 0.1 }}
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
>
  <div
    className="avatar"
    style={{ backgroundColor: getColor(index) }}
  >
    {uploadingId === member.id ? (
      <div className="avatar-loading">...</div>
    ) : member.avatar_url ? (
      <img src={`${import.meta.env.VITE_API_URL?.replace('/api', '') || 'http://localhost:8000'}${member.avatar_url}`} alt={member.name} />
    ) : (
      getInitials(member.name)
    )}
  </div>
  <span className="name">{member.name}</span>
</motion.button>
```

**Step 6: Add hidden file input**

Add before the closing `</div>` of the main component (before line 135):
```tsx
<input
  ref={fileInputRef}
  type="file"
  accept="image/*"
  onChange={handleFileChange}
  style={{ display: 'none' }}
/>
```

**Step 7: Add loading spinner CSS**

Add to end of `frontend/src/pages/UserSelect.css`:
```css
.avatar-loading {
  font-size: 1.5rem;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

**Step 8: Verify frontend builds**

Run: `cd /Users/tim/Claude/Movie_picker/frontend && npm run build`
Expected: Build succeeds with no errors

**Step 9: Commit**

```bash
git add frontend/src/pages/UserSelect.tsx frontend/src/pages/UserSelect.css
git commit -m "feat: add long-press avatar upload to UserSelect"
```

---

## Task 7: Integration Test

**Files:** None (manual testing)

**Step 1: Start backend server**

Run: `cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

**Step 2: Start frontend server**

Run: `cd /Users/tim/Claude/Movie_picker/frontend && npm run dev`

**Step 3: Manual test checklist**

1. Open http://localhost:5173 in browser
2. Long-press (or hold mouse) on a member avatar for ~500ms
3. File picker should open
4. Select an image from your device
5. Avatar should show "..." while uploading
6. After upload, avatar should display the new image
7. Refresh page - avatar should persist

**Step 4: Verify static file exists**

Run: `ls -la /Users/tim/Claude/Movie_picker/backend/static/avatars/`
Expected: Should see `{member_id}.jpg` file(s)

**Step 5: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: any integration fixes"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Add Pillow dependency | requirements.txt |
| 2 | Static file serving | main.py, static/avatars/.gitkeep |
| 3 | Write avatar tests | tests/test_avatar.py |
| 4 | Implement endpoint | routers/members.py |
| 5 | Frontend API function | api/client.ts |
| 6 | Long-press UI | UserSelect.tsx, UserSelect.css |
| 7 | Integration test | Manual testing |
