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
