# Ralph Wiggum Prompt: Implement Profile Avatar Upload

## Completion Promise
Output `<promise>AVATAR FEATURE COMPLETE</promise>` when ALL of these are true:
1. All 7 tasks from the implementation plan are complete
2. Backend tests pass (`pytest` from backend/)
3. Frontend builds without errors (`npm run build` from frontend/)
4. Avatar upload endpoint works (verified via curl or test)

## Implementation Plan Reference
Follow: `docs/plans/2026-01-02-profile-avatar-implementation.md`

## Task Checklist

Check git log and file state to determine progress. Complete tasks in order:

### Task 1: Pillow Dependency
- [ ] `Pillow>=10.0.0` in `backend/requirements.txt`
- [ ] Committed

### Task 2: Static File Serving
- [ ] `backend/static/avatars/.gitkeep` exists
- [ ] `backend/app/main.py` imports `StaticFiles` and `os`
- [ ] `backend/app/main.py` mounts `/static` directory
- [ ] Committed

### Task 3: Avatar Upload Tests
- [ ] `backend/tests/test_avatar.py` exists with 4 tests
- [ ] Tests currently fail (endpoint not implemented yet) OR pass (if Task 4 done)
- [ ] Committed

### Task 4: Avatar Upload Endpoint
- [ ] `backend/app/routers/members.py` has `upload_avatar` endpoint
- [ ] Endpoint handles: file validation, Pillow processing, center-crop, save to static
- [ ] `pytest tests/test_avatar.py -v` passes
- [ ] Committed

### Task 5: Frontend API Function
- [ ] `frontend/src/api/client.ts` has `uploadAvatar` function
- [ ] `npm run build` succeeds
- [ ] Committed

### Task 6: Long-Press UI
- [ ] `frontend/src/pages/UserSelect.tsx` has long-press handlers
- [ ] `frontend/src/pages/UserSelect.tsx` has hidden file input
- [ ] `frontend/src/pages/UserSelect.tsx` has upload mutation
- [ ] `frontend/src/pages/UserSelect.css` has `.avatar-loading` styles
- [ ] `npm run build` succeeds
- [ ] Committed

### Task 7: Final Verification
- [ ] `pytest` from backend/ - ALL tests pass
- [ ] `npm run build` from frontend/ - builds successfully
- [ ] Endpoint test: `curl -X POST -F "file=@<test_image>" http://localhost:8000/api/members/1/avatar` returns 200

## Iteration Strategy

Each iteration:
1. Check git log to see what's already committed
2. Read relevant files to assess current state
3. Identify the NEXT incomplete task
4. Implement that task following the detailed steps in the implementation plan
5. Run tests for that task
6. Commit if tests pass
7. Move to next task

## Important Notes

- The implementation plan has exact code snippets - use them
- Each task should be committed separately with descriptive messages
- If tests fail, fix the code before moving on
- If you're unsure what's done, check `git log --oneline -10`
- Backend venv: `source backend/venv/bin/activate`

## Verification Commands

```bash
# Backend tests
cd /Users/tim/Claude/Movie_picker/backend && source venv/bin/activate && pytest -v

# Frontend build
cd /Users/tim/Claude/Movie_picker/frontend && npm run build

# Quick endpoint test (after backend running)
curl -X POST -F "file=@backend/tests/test_avatar.py" http://localhost:8000/api/members/1/avatar 2>/dev/null | head -c 200
```

When all tasks complete and all verification passes, output:
`<promise>AVATAR FEATURE COMPLETE</promise>`
