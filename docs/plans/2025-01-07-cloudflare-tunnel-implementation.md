# Cloudflare Tunnel Implementation Checklist

**Reference:** `docs/plans/2025-01-07-cloudflare-tunnel-design.md`
**Status:** COMPLETE (2025-01-07)

## Prerequisites (Human Required)

These steps require human intervention before Ralph can proceed:

- [x] **HUMAN:** Create Cloudflare account at https://cloudflare.com (email verification required)
- [x] **HUMAN:** Add andofam.com to Cloudflare (Free plan)
- [x] **HUMAN:** Update nameservers at Squarespace to Cloudflare's nameservers
- [x] **HUMAN:** Wait for DNS propagation (Cloudflare emails when ready)
- [x] **HUMAN:** Create tunnel named `andofam-tunnel` in Zero Trust dashboard
- [x] **HUMAN:** Copy tunnel token and provide it when prompted

Once prerequisites are complete, set this flag:
- [x] PREREQUISITES_COMPLETE=true

## Phase 1: Tunnel Configuration (Browser - Cloudflare Dashboard)

**URL:** https://one.dash.cloudflare.com/ → Networks → Tunnels → andofam-tunnel

- [x] Configure public hostname:
  - Subdomain: `flix`
  - Domain: `andofam.com`
  - Type: HTTP
  - URL: `frontend:80`
- [x] Verify hostname saved in tunnel config
- [x] PHASE_1_COMPLETE=true

## Phase 2: Docker Compose Update (SSH/Files)

**Target:** LXC 103 at `/opt/familyflix`

- [x] Update `deploy/docker-compose.homelab.yml` to add cloudflared service:
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
- [x] Verify cloudflared service added correctly
- [x] PHASE_2_COMPLETE=true

## Phase 3: Deploy to Homelab (SSH)

**SSH Target:** `root@100.115.142.20` → `pct exec 103`

- [x] Sync updated docker-compose to LXC
- [x] Add CLOUDFLARE_TUNNEL_TOKEN to `/opt/familyflix/.env`
- [x] Run: `docker compose -f deploy/docker-compose.homelab.yml up -d`
- [x] Verify all containers running (backend, frontend, cloudflared)
- [x] Check cloudflared logs for "Connection registered"
- [x] PHASE_3_COMPLETE=true

## Phase 4: Cloudflare Access Setup (Browser)

**URL:** https://one.dash.cloudflare.com/ → Access → Applications

- [x] Create self-hosted application:
  - Name: `Family Flix`
  - Domain: `flix.andofam.com`
  - Session duration: 24 hours
- [x] Create access policies:
  - **Family Domains** (ALLOW): Emails ending in @andersonfamily.name, @andofam.com, @tjando.com
  - **Family Members** (ALLOW): Specific family member email addresses
- [x] Authentication method: One-time PIN (email OTP) - enabled by default
  - Note: Apple identity provider requires additional Apple Developer setup; email OTP works for all family members
- [x] PHASE_4_COMPLETE=true

## Phase 5: Verification (Browser + SSH)

- [x] Navigate to https://flix.andofam.com in browser
- [x] Verify Cloudflare Access login page appears
- [x] Email OTP sign-in option visible (Apple/Google can be added later if desired)
- [x] Verify Tailscale access still works: `http://mediastack-as.bone-egret.ts.net:8088` - HTTP 200

Remaining for user to verify:
- [ ] Test sign-in with authorized email (user should test)
- [ ] Verify Family Flix app loads after authentication (user should test)

- [x] PHASE_5_COMPLETE=true

## Completion Criteria

All phases must be complete:
- [x] PHASE_1_COMPLETE=true
- [x] PHASE_2_COMPLETE=true
- [x] PHASE_3_COMPLETE=true
- [x] PHASE_4_COMPLETE=true
- [x] PHASE_5_COMPLETE=true

## Summary

**Public URL:** https://flix.andofam.com
**Authentication:** Cloudflare Access with email OTP
**Access Policies:**
- Family Domains: @andersonfamily.name, @andofam.com, @tjando.com
- Family Members: honey@, evie@, beck@andersonfamily.name, monty@andofam.com, tim@tjando.com, toby@bottrall.com.au, tobiasbottrallmusic@gmail.com

**Tailscale Access:** Still functional at http://mediastack-as.bone-egret.ts.net:8088

---

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
