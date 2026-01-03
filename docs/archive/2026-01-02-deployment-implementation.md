# Deployment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create all deployment files and configure the app for production on Arthur's Seat homelab.

**Architecture:** Docker Compose with Tailscale sidecar for secure remote access. Nginx serves React frontend and proxies API to FastAPI backend. SQLite for persistence.

**Tech Stack:** Docker, Tailscale, Nginx, FastAPI, React, Vite

**Design Doc:** `docs/plans/2026-01-02-deployment-design.md`

---

## Task 1: Fix Frontend API Base URL

The current API client uses `http://localhost:8000/api` as default, which won't work in production behind Nginx proxy.

**Files:**
- Modify: `frontend/src/api/client.ts:15`

**Step 1: Update API_BASE to use relative URL**

Change line 15 from:
```typescript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
```

To:
```typescript
const API_BASE = import.meta.env.VITE_API_URL || '/api';
```

**Step 2: Verify dev still works with proxy**

For local development, Vite needs a proxy config. Check `vite.config.ts` - we'll add proxy in Task 2.

**Step 3: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "fix: use relative API URL for production deployment"
```

---

## Task 2: Add Vite Dev Proxy

Add proxy configuration so local development still routes `/api` to the backend.

**Files:**
- Modify: `frontend/vite.config.ts`

**Step 1: Update vite.config.ts**

Replace entire file with:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

**Step 2: Test local development**

```bash
cd frontend && npm run dev
# In another terminal:
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
```

Open http://localhost:5173 - app should work with API calls proxied.

**Step 3: Commit**

```bash
git add frontend/vite.config.ts
git commit -m "feat: add vite dev proxy for /api and /static"
```

---

## Task 3: Create PWA Icon (512px)

The manifest references `icon-512.png` but only `icon-192.png` exists.

**Files:**
- Create: `frontend/public/icon-512.png`

**Step 1: Generate 512px icon from existing 192px**

```bash
cd frontend/public
# Use ImageMagick to upscale (or create new icon)
convert icon-192.png -resize 512x512 icon-512.png
```

If ImageMagick not available, manually create a 512x512 PNG icon with the same design.

**Step 2: Verify icon exists**

```bash
ls -la frontend/public/icon-512.png
# Should show file ~50-100KB
```

**Step 3: Commit**

```bash
git add frontend/public/icon-512.png
git commit -m "feat: add 512px PWA icon"
```

---

## Task 4: Create Backend Dockerfile

**Files:**
- Create: `backend/Dockerfile`

**Step 1: Create Dockerfile**

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Pillow (avatar processing)
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create directories for persistent data
RUN mkdir -p /app/data /app/static/avatars

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Test Docker build**

```bash
cd backend
docker build -t familyflix-backend .
```

Expected: Build completes successfully.

**Step 3: Commit**

```bash
git add backend/Dockerfile
git commit -m "feat: add backend Dockerfile"
```

---

## Task 5: Create Frontend Dockerfile

**Files:**
- Create: `frontend/Dockerfile`

**Step 1: Create Dockerfile**

Create `frontend/Dockerfile`:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**Step 2: Commit (nginx.conf created in next task)**

```bash
git add frontend/Dockerfile
git commit -m "feat: add frontend Dockerfile with multi-stage build"
```

---

## Task 6: Create Nginx Configuration

**Files:**
- Create: `frontend/nginx.conf`

**Step 1: Create nginx.conf**

Create `frontend/nginx.conf`:
```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # API proxy to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (avatars)
    location /static/ {
        proxy_pass http://127.0.0.1:8000;
    }

    # SPA fallback - serve index.html for client-side routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
}
```

**Step 2: Test frontend Docker build**

```bash
cd frontend
docker build -t familyflix-frontend .
```

Expected: Build completes successfully.

**Step 3: Commit**

```bash
git add frontend/nginx.conf
git commit -m "feat: add nginx config for SPA and API proxy"
```

---

## Task 7: Create Tailscale Serve Configuration

**Files:**
- Create: `deploy/serve-config.json`

**Step 1: Create deploy directory and config**

```bash
mkdir -p deploy
```

Create `deploy/serve-config.json`:
```json
{
  "TCP": {
    "443": {
      "HTTPS": true
    }
  },
  "Web": {
    "${TS_CERT_DOMAIN}:443": {
      "Handlers": {
        "/": {
          "Proxy": "http://127.0.0.1:80"
        }
      }
    }
  }
}
```

**Step 2: Commit**

```bash
git add deploy/serve-config.json
git commit -m "feat: add Tailscale Serve config for HTTPS"
```

---

## Task 8: Create Docker Compose File

**Files:**
- Create: `deploy/docker-compose.yml`

**Step 1: Create docker-compose.yml**

Create `deploy/docker-compose.yml`:
```yaml
services:
  tailscale:
    image: tailscale/tailscale:latest
    container_name: familyflix-tailscale
    hostname: familyflix
    restart: unless-stopped
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_HOSTNAME=familyflix
      - TS_STATE_DIR=/var/lib/tailscale
      - TS_SERVE_CONFIG=/config/serve-config.json
      - TS_USERSPACE=false
    volumes:
      - tailscale-state:/var/lib/tailscale
      - ./serve-config.json:/config/serve-config.json:ro
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun:/dev/net/tun

  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    container_name: familyflix-frontend
    restart: unless-stopped
    network_mode: service:tailscale
    depends_on:
      - tailscale
      - backend

  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: familyflix-backend
    restart: unless-stopped
    network_mode: service:tailscale
    depends_on:
      - tailscale
    environment:
      - TMDB_API_KEY=${TMDB_API_KEY}
      - TMDB_ACCESS_TOKEN=${TMDB_ACCESS_TOKEN}
      - OMDB_API_KEY=${OMDB_API_KEY}
      - DATABASE_URL=sqlite:///data/family_flix.db
    volumes:
      - app-data:/app/data
      - app-static:/app/static

volumes:
  tailscale-state:
  app-data:
  app-static:
```

**Step 2: Commit**

```bash
git add deploy/docker-compose.yml
git commit -m "feat: add docker-compose with Tailscale sidecar"
```

---

## Task 9: Create Environment Template

**Files:**
- Create: `deploy/.env.example`

**Step 1: Create .env.example**

Create `deploy/.env.example`:
```env
# Tailscale auth key (generate at https://login.tailscale.com/admin/settings/keys)
# Create: Reusable, No expiry recommended
TS_AUTHKEY=tskey-auth-xxxxx

# TMDB API credentials (from https://www.themoviedb.org/settings/api)
TMDB_API_KEY=your_tmdb_api_key
TMDB_ACCESS_TOKEN=your_tmdb_access_token

# OMDb API key for Rotten Tomatoes scores (from https://www.omdbapi.com/apikey.aspx)
OMDB_API_KEY=your_omdb_api_key
```

**Step 2: Add .env to gitignore**

Verify `deploy/.env` is ignored (add to `.gitignore` if not):
```bash
echo "deploy/.env" >> .gitignore
```

**Step 3: Commit**

```bash
git add deploy/.env.example .gitignore
git commit -m "feat: add environment template for deployment"
```

---

## Task 10: Create Deployment README

**Files:**
- Create: `deploy/README.md`

**Step 1: Create README**

Create `deploy/README.md`:
```markdown
# Family Flix Deployment

Deploy to Arthur's Seat homelab (mediastack-as LXC 103).

## Prerequisites

- Docker and Docker Compose installed on target
- Tailscale auth key from https://login.tailscale.com/admin/settings/keys

## Quick Start

1. Copy files to server:
   ```bash
   scp -r . root@100.115.142.20:/tmp/familyflix-deploy
   ssh root@100.115.142.20 'pct exec 103 -- mkdir -p /opt/familyflix'
   ssh root@100.115.142.20 'pct push 103 /tmp/familyflix-deploy /opt/familyflix'
   ```

2. SSH into container:
   ```bash
   ssh root@100.115.142.20
   pct enter 103
   cd /opt/familyflix
   ```

3. Create `.env` from template:
   ```bash
   cp .env.example .env
   nano .env  # Add your actual keys
   chmod 600 .env
   ```

4. Build and start:
   ```bash
   docker compose up -d --build
   ```

5. Verify:
   ```bash
   docker logs familyflix-tailscale
   # Should show successful connection to tailnet
   ```

## Access

- URL: https://familyflix.bone-egret.ts.net
- Requires Tailscale connection

## Updates

```bash
cd /opt/familyflix
git pull
docker compose up -d --build
```

## Backup

Database is stored in Docker volume `app-data`.

Manual backup:
```bash
docker cp familyflix-backend:/app/data/family_flix.db ./backup_$(date +%Y%m%d).db
```
```

**Step 2: Commit**

```bash
git add deploy/README.md
git commit -m "docs: add deployment README"
```

---

## Task 11: Create .dockerignore Files

**Files:**
- Create: `backend/.dockerignore`
- Create: `frontend/.dockerignore`

**Step 1: Create backend .dockerignore**

Create `backend/.dockerignore`:
```
venv/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.coverage
htmlcov/
*.db
.env
.git/
tests/
```

**Step 2: Create frontend .dockerignore**

Create `frontend/.dockerignore`:
```
node_modules/
dist/
.git/
*.log
.env*
```

**Step 3: Commit**

```bash
git add backend/.dockerignore frontend/.dockerignore
git commit -m "feat: add .dockerignore files for efficient builds"
```

---

## Task 12: Test Full Docker Compose Build (Local)

**Files:** None (verification only)

**Step 1: Test builds without Tailscale**

Create a test compose file for local testing (don't commit):
```bash
cd deploy
cat > docker-compose.test.yml << 'EOF'
services:
  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    ports:
      - "8080:80"
    depends_on:
      - backend

  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - TMDB_API_KEY=${TMDB_API_KEY:-test}
      - TMDB_ACCESS_TOKEN=${TMDB_ACCESS_TOKEN:-test}
      - OMDB_API_KEY=${OMDB_API_KEY:-test}
      - DATABASE_URL=sqlite:///data/family_flix.db
    volumes:
      - ./test-data:/app/data
EOF
```

**Step 2: Run test build**

```bash
docker compose -f docker-compose.test.yml build
```

Expected: Both images build successfully.

**Step 3: Start and verify**

```bash
docker compose -f docker-compose.test.yml up -d
curl http://localhost:8080
curl http://localhost:8000/api/members
```

Expected: Frontend returns HTML, backend returns JSON (empty array or member list).

**Step 4: Cleanup**

```bash
docker compose -f docker-compose.test.yml down
rm docker-compose.test.yml
rm -rf test-data
```

---

## Task 13: Final Commit - All Deployment Files

**Step 1: Verify all files**

```bash
git status
```

Expected: All deployment files committed in previous tasks.

**Step 2: Tag release**

```bash
git tag -a v1.0.0-deploy -m "Ready for homelab deployment"
```

---

## Post-Implementation: Server Deployment

After all tasks complete, follow `deploy/README.md` to:

1. Generate Tailscale auth key (reusable, no expiry)
2. Copy files to Arthur's Seat mediastack-as LXC
3. Create `.env` with real API keys
4. Run `docker compose up -d --build`
5. Verify at https://familyflix.bone-egret.ts.net
6. Invite family members to Tailscale
7. Help them add PWA to home screen
