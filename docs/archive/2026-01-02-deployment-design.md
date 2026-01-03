# Family Flix Picker Deployment Design

## Overview

Deploy the Family Flix Picker application to the Arthur's Seat Proxmox homelab with secure remote access via Tailscale.

**Target URL:** `https://familyflix.bone-egret.ts.net`

## Architecture

### Deployment Location

- **Host:** Arthur's Seat Proxmox → mediastack-as LXC (103)
- **Rationale:** Co-located with movie theater and media stack (Jellyfin, *arr apps)

### Container Structure

```
mediastack-as LXC 103
├── Existing containers (Jellyfin, Sonarr, Radarr, etc.)
└── Family Flix stack (new docker-compose)
    ├── tailscale (sidecar - provides network identity)
    ├── backend (FastAPI + SQLite)
    └── frontend (Nginx serving React build)
```

### Network Flow

```
Family phone (Tailscale)
  → https://familyflix.bone-egret.ts.net
  → Tailscale sidecar container (terminates HTTPS)
  → Nginx (frontend on port 80, proxies /api to backend)
  → FastAPI backend (port 8000)
```

### Resource Estimate

| Container | Memory |
|-----------|--------|
| Tailscale sidecar | ~20MB |
| Backend (FastAPI + SQLite) | ~100-200MB |
| Frontend (Nginx) | ~10MB |
| **Total** | **~250MB** |

mediastack-as has 8GB allocated - plenty of headroom.

## Remote Access Strategy

### Tailscale Sidecar Pattern

Native hostname aliases aren't supported in Tailscale (still an open feature request). The sidecar pattern gives each Docker service its own Tailscale identity with a clean hostname.

**How it works:**
- Tailscale container joins tailnet as `familyflix`
- Frontend and backend use `network_mode: service:tailscale`
- All containers share the sidecar's network interface
- Tailscale Serve handles HTTPS termination automatically

### Family Access

- Add family members to Tailscale tailnet (full access)
- Each family member installs Tailscale app on phone
- Bonus: They also get access to Jellyfin for remote streaming

## Docker Compose Configuration

**File location:** `/opt/familyflix/docker-compose.yml`

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
      - ./tailscale-state:/var/lib/tailscale
      - ./serve-config.json:/config/serve-config.json:ro
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun:/dev/net/tun

  frontend:
    build: ./frontend
    container_name: familyflix-frontend
    restart: unless-stopped
    network_mode: service:tailscale
    depends_on:
      - tailscale
      - backend

  backend:
    build: ./backend
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
      - ./data:/app/data
      - ./static:/app/static
```

## Tailscale Serve Configuration

**File:** `serve-config.json`

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

## Nginx Configuration

**File:** `frontend/nginx.conf`

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

## Dockerfiles

### Frontend Dockerfile

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

### Backend Dockerfile

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

## Directory Structure

```
/opt/familyflix/
├── docker-compose.yml
├── .env                    # Secrets (chmod 600)
├── serve-config.json       # Tailscale Serve config
├── tailscale-state/        # Persistent Tailscale identity
├── data/
│   └── family_flix.db      # SQLite database
├── static/
│   └── avatars/            # Uploaded member avatars
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/                # FastAPI application
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    └── src/                # React application
```

## Environment Variables

**File:** `.env`

```env
# Tailscale (generate at https://login.tailscale.com/admin/settings/keys)
TS_AUTHKEY=tskey-auth-xxxxx

# TMDB API
TMDB_API_KEY=your_tmdb_api_key
TMDB_ACCESS_TOKEN=your_tmdb_access_token

# OMDb API (for Rotten Tomatoes scores)
OMDB_API_KEY=your_omdb_api_key
```

## Deployment Steps

### Initial Deployment

```bash
# 1. SSH into the mediastack LXC
ssh root@100.115.142.20
pct enter 103

# 2. Create application directory
mkdir -p /opt/familyflix
cd /opt/familyflix

# 3. Copy/clone application files
# (scp or git clone from dev machine)

# 4. Generate Tailscale auth key
# Visit: https://login.tailscale.com/admin/settings/keys
# Create: Reusable, No expiry, tag:container (optional)

# 5. Create .env file with secrets
cat > .env << 'EOF'
TS_AUTHKEY=tskey-auth-xxxxx
TMDB_API_KEY=your_key
TMDB_ACCESS_TOKEN=your_token
OMDB_API_KEY=your_key
EOF
chmod 600 .env

# 6. Build and start
docker compose up -d --build

# 7. Verify Tailscale joined
docker logs familyflix-tailscale
```

### Updating the App

```bash
cd /opt/familyflix
git pull                      # or scp new files
docker compose up -d --build  # Rebuild and restart
```

## Family Onboarding

### Adding Family to Tailscale

1. **Send invite:**
   - Go to https://login.tailscale.com/admin/users
   - Click "Invite users"
   - Enter family member's email

2. **Family member setup (phone):**
   - Receives email invite
   - Downloads Tailscale app (iOS App Store / Google Play)
   - Opens app, signs in with their email
   - Approves connection to tailnet

3. **Approve if required:**
   - Admin console → Machines → Approve

### Creating Phone Shortcut (PWA)

**iOS Safari:**
1. Navigate to `https://familyflix.bone-egret.ts.net`
2. Tap Share button → "Add to Home Screen"
3. Name it "Family Flix" → Add

**Android Chrome:**
1. Navigate to `https://familyflix.bone-egret.ts.net`
2. Tap menu (⋮) → "Add to Home screen"
3. Name it "Family Flix" → Add

## Backup Strategy

### What Needs Backing Up

| Data | Location | Criticality |
|------|----------|-------------|
| SQLite database | `/opt/familyflix/data/family_flix.db` | High |
| Avatar uploads | `/opt/familyflix/static/avatars/` | Medium |
| Tailscale state | `/opt/familyflix/tailscale-state/` | Low |
| Config/code | `/opt/familyflix/` | Low (in git) |

### Backup Methods

**Proxmox vzdump (automatic):**
- LXC 103 included in weekly Proxmox backups
- Captures entire container

**Daily to Synology NAS (recommended):**
```bash
# Add to crontab on LXC 103
0 3 * * * cp /opt/familyflix/data/family_flix.db /mnt/nas/backups/familyflix/family_flix_$(date +\%Y\%m\%d).db
0 4 * * * find /mnt/nas/backups/familyflix -name "*.db" -mtime +7 -delete
```

### Recovery

```bash
docker compose down
cp /mnt/nas/backups/familyflix/family_flix_YYYYMMDD.db ./data/family_flix.db
docker compose up -d
```

## Additional Considerations

### Frontend API Configuration

Verify `frontend/src/api/client.ts` uses relative URLs:
```typescript
const API_BASE = '/api';  // Works behind Nginx proxy
```

### PWA Manifest

Update `frontend/public/manifest.json`:
```json
{
  "name": "Family Flix Picker",
  "short_name": "Family Flix",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1a1a2e",
  "theme_color": "#e94560",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### Monitoring (Optional)

Add to Homepage dashboard:
```yaml
- Family Flix:
    icon: mdi-movie-open
    href: https://familyflix.bone-egret.ts.net
    description: Movie picker
```

### Security Notes

- No public ports exposed - Tailscale only
- API keys stored in `.env` with 600 permissions
- Family authenticated via Tailscale identity
- Zero-trust network design

### Potential Issues

| Issue | Mitigation |
|-------|------------|
| Tailscale auth key expiry | Use "No expiry" key |
| Database grows large | SQLite handles 10K+ movies fine |
| TMDB rate limits | 40 req/10s is generous for family use |
| Container restart order | `depends_on` ensures correct startup |
