# Deployment Implementation - Ralph Loop Prompt

## Your Mission

Execute the implementation plan at `docs/plans/2026-01-02-deployment-implementation.md` autonomously until ALL 13 tasks are complete and verified.

## How to Work

1. **Read the plan** - Start by reading `docs/plans/2026-01-02-deployment-implementation.md`
2. **Check progress** - Use `git log --oneline -20` to see what's already done
3. **Find next incomplete task** - Work through tasks 1-13 in order
4. **Execute the task** - Follow the exact steps in the plan
5. **Commit after each task** - Use the commit messages specified in the plan
6. **Track with TodoWrite** - Update the todo list as you complete tasks

## Task Checklist

Track these in your TodoWrite:

- [ ] Task 1: Fix frontend API base URL to `/api`
- [ ] Task 2: Add Vite dev proxy configuration
- [ ] Task 3: Create 512px PWA icon
- [ ] Task 4: Create backend Dockerfile
- [ ] Task 5: Create frontend Dockerfile
- [ ] Task 6: Create Nginx configuration
- [ ] Task 7: Create Tailscale serve-config.json
- [ ] Task 8: Create docker-compose.yml
- [ ] Task 9: Create .env.example template
- [ ] Task 10: Create deployment README
- [ ] Task 11: Create .dockerignore files
- [ ] Task 12: Test Docker Compose build locally
- [ ] Task 13: Tag release v1.0.0-deploy

## Completion Criteria

ALL of these must be true before outputting the completion promise:

1. All 13 tasks from the implementation plan are complete
2. All files exist:
   - `frontend/src/api/client.ts` - uses `/api` as default base
   - `frontend/vite.config.ts` - has proxy config
   - `frontend/public/icon-512.png` - exists
   - `frontend/Dockerfile` - exists
   - `frontend/nginx.conf` - exists
   - `frontend/.dockerignore` - exists
   - `backend/Dockerfile` - exists
   - `backend/.dockerignore` - exists
   - `deploy/docker-compose.yml` - exists
   - `deploy/serve-config.json` - exists
   - `deploy/.env.example` - exists
   - `deploy/README.md` - exists
3. Docker builds succeed: `docker compose -f deploy/docker-compose.test.yml build` (create test compose without Tailscale)
4. Git tag `v1.0.0-deploy` exists

## Verification Commands

Run these to verify completion:

```bash
# Check all files exist
ls -la frontend/Dockerfile frontend/nginx.conf frontend/.dockerignore
ls -la backend/Dockerfile backend/.dockerignore
ls -la deploy/docker-compose.yml deploy/serve-config.json deploy/.env.example deploy/README.md
ls -la frontend/public/icon-512.png

# Check API client uses relative URL
grep "const API_BASE" frontend/src/api/client.ts

# Check vite has proxy
grep -A5 "proxy:" frontend/vite.config.ts

# Check Docker builds work
cd deploy && docker compose -f docker-compose.test.yml build 2>&1 | tail -5

# Check git tag
git tag -l "v1.0.0-deploy"
```

## When Complete

When ALL criteria are met, output:

```
<promise>DEPLOYMENT IMPLEMENTATION COMPLETE</promise>
```

## Important Notes

- Follow the implementation plan exactly - it has the correct file contents
- Commit after EACH task (not batched)
- If a task is already done (check git log), skip to the next
- If Docker build fails, debug and fix before continuing
- For Task 3 (icon), if ImageMagick isn't available, create a simple placeholder or skip

## Current Status

Check git log to see what's already been done:
```bash
git log --oneline -20
```

Then continue from where you left off.
