# Family Flix Picker - Homelab Deployment

Deploy to Arthur's Seat homelab (mediastack-as LXC 103).

## Access

### Public Access (via Cloudflare Tunnel)
- **URL**: `https://flix.andofam.com`
- **Authentication**: Cloudflare Access (email OTP)
- **Session**: 1 month (sign in once per month)
- **Allowed**: Family email domains (@andersonfamily.name, @andofam.com, @tjando.com)

**To sign in:** Enter your email → Click "Send me a code" → Check email for code from Cloudflare → Enter code

### Internal Access (via Tailscale)
- **URL**: `http://mediastack-as.bone-egret.ts.net:8088`
- **Requires**: Tailscale connection to bone-egret tailnet

## Deployment Methods

### Method 1: Automated Script (Recommended)

```bash
cd deploy
chmod +x deploy.sh

# First deployment:
./deploy.sh --first-run

# Subsequent deployments:
./deploy.sh
```

### Method 2: Manual Deployment

#### First-Time Setup

1. SSH into the LXC container:
   ```bash
   ssh root@100.115.142.20
   pct enter 103
   mkdir -p /opt/familyflix
   ```

2. Copy files (from local machine):
   ```bash
   rsync -avz --exclude '.git' --exclude 'node_modules' --exclude 'venv' \
     ./ root@100.115.142.20:/tmp/familyflix/
   ssh root@100.115.142.20 'pct push 103 /tmp/familyflix /opt/familyflix'
   ```

3. Configure environment:
   ```bash
   # In LXC container:
   cd /opt/familyflix
   cp .env.example .env
   nano .env  # Add your API keys
   chmod 600 .env
   ```

4. Start services:
   ```bash
   docker compose up -d --build
   ```

#### Updating an Existing Deployment

```bash
./deploy.sh
```

Or manually:
```bash
ssh root@100.115.142.20 'pct exec 103 -- bash -c "cd /opt/familyflix && docker compose down && docker compose build --no-cache && docker compose up -d"'
```

## Environment Variables

Create `.env` in `/opt/familyflix/` with:

| Variable | Source |
|----------|--------|
| `TMDB_API_KEY` | https://www.themoviedb.org/settings/api |
| `TMDB_ACCESS_TOKEN` | TMDB API settings (Bearer token) |
| `OMDB_API_KEY` | https://www.omdbapi.com/apikey.aspx |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Access Methods                            │
├─────────────────────────────┬───────────────────────────────┤
│  Public (Cloudflare Tunnel) │  Internal (Tailscale)         │
│  https://flix.andofam.com   │  http://mediastack-as:8088    │
│         │                   │           │                   │
│         ▼                   │           │                   │
│  ┌─────────────────┐        │           │                   │
│  │ Cloudflare Edge │        │           │                   │
│  │ Access Auth     │        │           │                   │
│  └────────┬────────┘        │           │                   │
│           │                 │           │                   │
└───────────┼─────────────────┴───────────┼───────────────────┘
            │                             │
            ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│ LXC 103 (mediastack-as)                                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ cloudflared  │  │  frontend    │──│     backend      │   │
│  │ (tunnel)     │──│  (Nginx:80)  │  │  (FastAPI:8000)  │   │
│  └──────────────┘  │   :8088      │  │                  │   │
│                    └──────────────┘  └──────────────────┘   │
│                           │                  │               │
│                           ▼                  ▼               │
│                    familyflix-data    familyflix-static      │
└─────────────────────────────────────────────────────────────┘
```

## Container Management

Check status:
```bash
ssh root@100.115.142.20 'pct exec 103 -- docker ps --filter name=familyflix'
```

View logs:
```bash
ssh root@100.115.142.20 'pct exec 103 -- docker logs -f familyflix-backend'
ssh root@100.115.142.20 'pct exec 103 -- docker logs -f familyflix-frontend'
ssh root@100.115.142.20 'pct exec 103 -- docker logs -f familyflix-cloudflared'
```

Restart services:
```bash
ssh root@100.115.142.20 'pct exec 103 -- bash -c "cd /opt/familyflix && docker compose restart"'
```

Stop services:
```bash
ssh root@100.115.142.20 'pct exec 103 -- bash -c "cd /opt/familyflix && docker compose down"'
```

## Backup & Restore

### Backup Database + Avatars

Use SQLite's online `.backup` command so the snapshot is consistent even while
the app is writing. Then also snapshot the avatar volume — it isn't worth
losing custom avatars to a torn copy.

```bash
DATE=$(date +%Y%m%d)

# 1. Consistent SQLite snapshot (no need to stop the backend)
ssh root@100.115.142.20 "pct exec 103 -- docker exec familyflix-backend \
  sqlite3 /app/data/family_flix.db \".backup /app/data/backup.db\""
ssh root@100.115.142.20 "pct exec 103 -- docker cp familyflix-backend:/app/data/backup.db /tmp/family_flix_${DATE}.db"
scp root@100.115.142.20:/tmp/family_flix_${DATE}.db ./

# 2. Avatars (tar from the named volume)
ssh root@100.115.142.20 "pct exec 103 -- docker run --rm -v familyflix-static:/data alpine \
  tar -czf - -C /data . > /tmp/familyflix_static_${DATE}.tar.gz"
scp root@100.115.142.20:/tmp/familyflix_static_${DATE}.tar.gz ./

# Clean up remote temp files
ssh root@100.115.142.20 "pct exec 103 -- rm -f /tmp/family_flix_${DATE}.db /tmp/familyflix_static_${DATE}.tar.gz"
```

### Restore Database + Avatars

```bash
DATE=20260101  # adjust to your backup

# 1. Database (stop backend during swap)
scp ./family_flix_${DATE}.db root@100.115.142.20:/tmp/restore.db
ssh root@100.115.142.20 'pct exec 103 -- docker compose -f /opt/familyflix/docker-compose.yml stop backend'
ssh root@100.115.142.20 'pct exec 103 -- docker cp /tmp/restore.db familyflix-backend:/app/data/family_flix.db'

# 2. Avatars
scp ./familyflix_static_${DATE}.tar.gz root@100.115.142.20:/tmp/restore-static.tar.gz
ssh root@100.115.142.20 "pct exec 103 -- docker run --rm -v familyflix-static:/data -v /tmp:/backup alpine \
  sh -c 'rm -rf /data/* && tar -xzf /backup/restore-static.tar.gz -C /data'"

ssh root@100.115.142.20 'pct exec 103 -- docker compose -f /opt/familyflix/docker-compose.yml start backend'
```

## Port Allocation

Family Flix uses port **8088** on the mediastack LXC. Other services:

| Service | Port |
|---------|------|
| Jellyseerr | 5055 |
| Bazarr | 6767 |
| Radarr | 7878 |
| qBittorrent | 8080 |
| **Family Flix** | **8088** |
| Jellyfin | 8096 |
| Sonarr | 8989 |
| Prowlarr | 9696 |

## Troubleshooting

**Container won't start:**
```bash
ssh root@100.115.142.20 'pct exec 103 -- docker logs familyflix-backend'
```

**Health check failing:**
```bash
ssh root@100.115.142.20 'pct exec 103 -- docker exec familyflix-backend curl http://localhost:8000/api/health'
```

**Rebuild from scratch:**
```bash
ssh root@100.115.142.20 'pct exec 103 -- bash -c "cd /opt/familyflix && docker compose down -v && docker compose build --no-cache && docker compose up -d"'
```

**Check disk space:**
```bash
ssh root@100.115.142.20 'pct exec 103 -- df -h'
```
