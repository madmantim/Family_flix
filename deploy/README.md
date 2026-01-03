# Family Flix Picker - Homelab Deployment

Deploy to Arthur's Seat homelab (mediastack-as LXC 103).

## Access

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
┌─────────────────────────────────────────────────────┐
│ Family devices (Tailscale)                          │
│         │                                           │
│         ▼                                           │
│ mediastack-as.bone-egret.ts.net:8088                │
│         │                                           │
│         ▼                                           │
│ ┌─────────────────────────────────────────────────┐ │
│ │ LXC 103 (mediastack-as)                         │ │
│ │                                                 │ │
│ │  ┌──────────────┐     ┌──────────────────────┐  │ │
│ │  │  frontend    │────▶│     backend          │  │ │
│ │  │  (Nginx:80)  │     │  (FastAPI:8000)      │  │ │
│ │  │   :8088      │     │                      │  │ │
│ │  └──────────────┘     └──────────────────────┘  │ │
│ │         ▲                     │                 │ │
│ │         │                     ▼                 │ │
│ │         │              familyflix-data          │ │
│ │         │              familyflix-static        │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
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

### Backup Database

```bash
# Copy from container
ssh root@100.115.142.20 'pct exec 103 -- docker cp familyflix-backend:/app/data/family_flix.db /tmp/backup.db'
scp root@100.115.142.20:/tmp/backup.db ./family_flix_backup_$(date +%Y%m%d).db
```

### Restore Database

```bash
# Copy to container (stops service first)
scp ./backup.db root@100.115.142.20:/tmp/restore.db
ssh root@100.115.142.20 'pct exec 103 -- docker compose -f /opt/familyflix/docker-compose.yml stop backend'
ssh root@100.115.142.20 'pct exec 103 -- docker cp /tmp/restore.db familyflix-backend:/app/data/family_flix.db'
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
