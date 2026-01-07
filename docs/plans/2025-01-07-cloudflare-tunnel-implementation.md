# Cloudflare Tunnel Implementation Checklist

**Reference:** `docs/plans/2025-01-07-cloudflare-tunnel-design.md`

## Prerequisites (Human Required)

These steps require human intervention before Ralph can proceed:

- [ ] **HUMAN:** Create Cloudflare account at https://cloudflare.com (email verification required)
- [ ] **HUMAN:** Add andofam.com to Cloudflare (Free plan)
- [ ] **HUMAN:** Update nameservers at Squarespace to Cloudflare's nameservers
- [ ] **HUMAN:** Wait for DNS propagation (Cloudflare emails when ready)
- [ ] **HUMAN:** Create tunnel named `andofam-tunnel` in Zero Trust dashboard
- [ ] **HUMAN:** Copy tunnel token and provide it when prompted

Once prerequisites are complete, set this flag:
- [ ] PREREQUISITES_COMPLETE=true

## Phase 1: Tunnel Configuration (Browser - Cloudflare Dashboard)

**URL:** https://one.dash.cloudflare.com/ → Networks → Tunnels → andofam-tunnel

- [ ] Configure public hostname:
  - Subdomain: `flix`
  - Domain: `andofam.com`
  - Type: HTTP
  - URL: `frontend:80`
- [ ] Verify hostname saved in tunnel config
- [ ] PHASE_1_COMPLETE=true

## Phase 2: Docker Compose Update (SSH/Files)

**Target:** LXC 103 at `/opt/familyflix`

- [ ] Update `deploy/docker-compose.homelab.yml` to add cloudflared service:
  ```yaml
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: familyflix-cloudflared
    restart: unless-stopped
    command: tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}
    networks:
      - familyflix
    depends_on:
      - frontend
  ```
- [ ] Verify cloudflared service added correctly
- [ ] PHASE_2_COMPLETE=true

## Phase 3: Deploy to Homelab (SSH)

**SSH Target:** `root@100.115.142.20` → `pct exec 103`

- [ ] Sync updated docker-compose to LXC
- [ ] Add CLOUDFLARE_TUNNEL_TOKEN to `/opt/familyflix/.env`
- [ ] Run: `docker compose -f deploy/docker-compose.homelab.yml up -d`
- [ ] Verify all containers running (backend, frontend, cloudflared)
- [ ] Check cloudflared logs for "Connection registered"
- [ ] PHASE_3_COMPLETE=true

## Phase 4: Cloudflare Access Setup (Browser)

**URL:** https://one.dash.cloudflare.com/ → Access → Applications

- [ ] Create self-hosted application:
  - Name: `Family Flix`
  - Domain: `flix.andofam.com`
  - Session duration: 7 days
- [ ] Create access policy:
  - Name: `Family Members`
  - Action: Allow
  - Include: Emails (family member list)
- [ ] Enable Apple identity provider (Settings → Authentication)
- [ ] PHASE_4_COMPLETE=true

## Phase 5: Verification (Browser + SSH)

- [ ] Test: `curl -I https://flix.andofam.com` returns 302 (redirect to Access login)
- [ ] Navigate to https://flix.andofam.com in browser
- [ ] Verify Cloudflare Access login page appears
- [ ] Verify Apple sign-in option visible
- [ ] Test sign-in with authorized email
- [ ] Verify Family Flix app loads after authentication
- [ ] Verify Tailscale access still works: `http://mediastack-as.bone-egret.ts.net:8088`
- [ ] PHASE_5_COMPLETE=true

## Completion Criteria

All phases must be complete:
- [ ] PHASE_1_COMPLETE=true
- [ ] PHASE_2_COMPLETE=true
- [ ] PHASE_3_COMPLETE=true
- [ ] PHASE_4_COMPLETE=true
- [ ] PHASE_5_COMPLETE=true

When ALL verification tests pass:
```
<promise>CLOUDFLARE_TUNNEL_COMPLETE</promise>
```

## Troubleshooting

### Tunnel not connecting
```bash
pct exec 103 -- docker logs familyflix-cloudflared
```
- Check token is correct in .env
- Verify container is on familyflix network

### 502 Bad Gateway
- Verify frontend container is healthy
- Check URL is `frontend:80` not `localhost:8088`

### Access policy not working
- Verify email addresses match exactly
- Check application domain matches `flix.andofam.com`

## Rollback

If issues persist:
```bash
pct exec 103 -- docker stop familyflix-cloudflared
```
Tailscale access remains functional at `http://mediastack-as.bone-egret.ts.net:8088`
