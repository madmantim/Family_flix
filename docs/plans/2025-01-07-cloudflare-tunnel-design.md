# Cloudflare Tunnel Setup for Family Flix

**Date:** 2025-01-07
**Status:** Design complete, ready for implementation

## Overview

Expose Family Flix Picker via Cloudflare Tunnel with Cloudflare Access authentication, enabling family members to access the app without Tailscale installed on their devices.

### Goals

- Public URL: `flix.andofam.com`
- Authentication via Apple/Google sign-in (Cloudflare Access)
- No firewall ports opened (outbound tunnel only)
- Foundation for exposing additional apps later

### Current State

- **Location:** Arthur's Seat homelab, Proxmox Mini-PC
- **Container:** LXC 103 (mediastack-as)
- **App path:** `/opt/familyflix`
- **Current access:** `http://mediastack-as.bone-egret.ts.net:8088` (Tailscale)
- **Domain:** andofam.com (registered at Squarespace)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Arthur's Seat Homelab                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                 Proxmox Mini-PC                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │              LXC 103 (mediastack-as)                      │  │ │
│  │  │                                                           │  │ │
│  │  │  Docker Network: familyflix                               │  │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐  │  │ │
│  │  │  │  frontend   │  │  backend    │  │  cloudflared     │  │  │ │
│  │  │  │  (Nginx:80) │◄─│  (:8000)    │  │  (new container) │  │  │ │
│  │  │  │             │  │             │  │                  │  │  │ │
│  │  │  └─────────────┘  └─────────────┘  └────────┬─────────┘  │  │ │
│  │  │        ▲                                     │            │  │ │
│  │  │        │ http://frontend:80                  │            │  │ │
│  │  │        └─────────────────────────────────────┘            │  │ │
│  │  │                                              │            │  │ │
│  │  └──────────────────────────────────────────────┼────────────┘  │ │
│  └─────────────────────────────────────────────────┼───────────────┘ │
└────────────────────────────────────────────────────┼─────────────────┘
                                                     │
                                                     │ Outbound HTTPS
                                                     │ (no inbound ports)
                                                     ▼
                                         ┌───────────────────────┐
                                         │   Cloudflare Edge     │
                                         │                       │
                                         │  ┌─────────────────┐  │
                                         │  │ Access Policy   │  │
                                         │  │ "Family only"   │  │
                                         │  │ Apple/Google    │  │
                                         │  └─────────────────┘  │
                                         │                       │
                                         │  flix.andofam.com     │
                                         └───────────────────────┘
                                                     │
                                                     ▼
                                         ┌───────────────────────┐
                                         │   Family Members      │
                                         │   Any device/browser  │
                                         │   Sign in with Apple  │
                                         └───────────────────────┘
```

### Verified Routing

| Component | Port | Notes |
|-----------|------|-------|
| Frontend (Nginx) | 80 (container), 8088 (LXC host) | Serves app + proxies /api |
| Backend (FastAPI) | 8000 | Internal only, not exposed |
| cloudflared | N/A | Outbound only, joins Docker network |

**Cloudflared routes to:** `http://frontend:80` (Docker service name)

## Implementation Phases

### Phase 1: Cloudflare Account & Domain (~15 min + propagation)

#### Step 1.1: Create Cloudflare Account
1. Go to https://cloudflare.com
2. Click "Sign Up"
3. Enter email and password
4. Verify email

#### Step 1.2: Add Domain to Cloudflare
1. Dashboard → "Add a site"
2. Enter: `andofam.com`
3. Select **Free** plan
4. Cloudflare scans existing DNS records automatically
5. Review imported records - ensure nothing is missing

#### Step 1.3: Update Nameservers at Squarespace
1. Cloudflare displays two nameservers (e.g., `ada.ns.cloudflare.com`, `bolt.ns.cloudflare.com`)
2. Log into Squarespace
3. Navigate: Domains → andofam.com → DNS Settings → Nameservers
4. Change from Squarespace nameservers to Cloudflare nameservers
5. Save changes

#### Step 1.4: Wait for Propagation
- Cloudflare emails when active (typically 5-30 minutes)
- Can take up to 24 hours in rare cases
- Check status in Cloudflare dashboard

**Note:** Existing services using andofam.com continue working - Cloudflare proxies existing DNS records.

---

### Phase 2: Create Tunnel (~10 min)

#### Step 2.1: Access Zero Trust Dashboard
1. In Cloudflare dashboard, click "Zero Trust" in left sidebar
2. First time setup:
   - Choose a team name: `andofam`
   - This creates: `andofam.cloudflareaccess.com`
   - Select Free plan (50 users included)

#### Step 2.2: Create the Tunnel
1. Zero Trust → Networks → Tunnels
2. Click "Create a tunnel"
3. Select connector type: **Cloudflared**
4. Name: `andofam-tunnel`
5. Click "Save tunnel"

#### Step 2.3: Get Tunnel Token
1. Cloudflare shows installation options
2. Select "Docker"
3. Copy the token from the command shown:
   ```
   docker run cloudflare/cloudflared:latest tunnel --no-autoupdate run --token eyJhIjoiNjk...
   ```
4. Save this token securely - you'll add it to your environment

#### Step 2.4: Configure Public Hostname
1. In tunnel configuration, go to "Public Hostname" tab
2. Click "Add a public hostname"
3. Configure:
   - **Subdomain:** `flix`
   - **Domain:** `andofam.com`
   - **Type:** HTTP
   - **URL:** `frontend:80`
4. Save

This tells Cloudflare: route `flix.andofam.com` → tunnel → `frontend:80`

---

### Phase 3: Deploy cloudflared (~10 min)

#### Step 3.1: Update docker-compose.homelab.yml

Add the cloudflared service to `/opt/familyflix/deploy/docker-compose.homelab.yml`:

```yaml
services:
  backend:
    # ... existing backend config ...

  frontend:
    # ... existing frontend config ...

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

#### Step 3.2: Add Token to Environment

Add to `/opt/familyflix/.env`:

```bash
# Existing variables
TMDB_API_KEY=...
TMDB_ACCESS_TOKEN=...
OMDB_API_KEY=...

# New: Cloudflare Tunnel
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiNjk...  # Your token from Phase 2
```

#### Step 3.3: Deploy

SSH into the LXC and redeploy:

```bash
ssh root@100.115.142.20
pct exec 103 -- bash -c "cd /opt/familyflix && docker compose -f deploy/docker-compose.homelab.yml up -d"
```

Or use the deploy script after updating the compose file locally:
```bash
cd deploy && ./deploy.sh
```

#### Step 3.4: Verify Tunnel Connection

1. Check container is running:
   ```bash
   pct exec 103 -- docker ps --filter name=cloudflared
   ```

2. Check tunnel logs:
   ```bash
   pct exec 103 -- docker logs familyflix-cloudflared
   ```
   Look for: "Connection registered" or "Tunnel is connected"

3. In Cloudflare dashboard: Zero Trust → Networks → Tunnels
   - Status should show "Healthy"

---

### Phase 4: Configure Cloudflare Access (~10 min)

#### Step 4.1: Enable Identity Providers

1. Zero Trust → Settings → Authentication
2. Click "Add new" under Login methods
3. Add **Apple:**
   - Click "Apple"
   - Follow prompts (Apple requires creating an App ID - Cloudflare guides you through it)
4. Optionally add **Google:**
   - Click "Google"
   - Follow OAuth setup if desired
5. **One-time PIN** is enabled by default (email code fallback)

#### Step 4.2: Create Access Application

1. Zero Trust → Access → Applications
2. Click "Add an application"
3. Select "Self-hosted"
4. Configure:
   - **Application name:** Family Flix
   - **Session duration:** 24 hours (or longer for convenience)
   - **Application domain:** `flix.andofam.com`

#### Step 4.3: Create Access Policy

1. Policy name: `Family Members`
2. Action: **Allow**
3. Configure rules - Include:
   - **Selector:** Emails
   - **Value:** Add each family member's email:
     ```
     tim@example.com
     spouse@example.com
     kid1@example.com
     kid2@example.com
     ```
4. Save policy
5. Save application

#### Step 4.4: Test Access

1. Open `https://flix.andofam.com` in a browser
2. You should see Cloudflare Access login screen
3. Sign in with Apple (or Google/email code)
4. After authentication, Family Flix loads

---

## Verification Checklist

- [ ] Cloudflare account created
- [ ] andofam.com added to Cloudflare
- [ ] Nameservers updated at Squarespace
- [ ] DNS propagation complete
- [ ] Tunnel created in Zero Trust dashboard
- [ ] Tunnel token saved to `.env`
- [ ] cloudflared container added to docker-compose
- [ ] Containers deployed and running
- [ ] Tunnel shows "Healthy" in dashboard
- [ ] Apple identity provider configured
- [ ] Access application created for `flix.andofam.com`
- [ ] Family member emails added to policy
- [ ] Test login works from a non-Tailscale device

## Future Expansion

Once this setup is working, adding more apps is straightforward:

### Add Another App (e.g., Jellyfin)

1. **Add hostname to existing tunnel:**
   - Zero Trust → Tunnels → andofam-tunnel → Public Hostname
   - Add: `jellyfin.andofam.com` → `localhost:8096`

2. **Create Access application:**
   - New self-hosted app for `jellyfin.andofam.com`
   - Same or different access policy

3. **No changes needed to cloudflared container** - it handles multiple hostnames

### Add Business Apps

For staff-only apps, create separate Access policies:
- Policy: "Staff Only"
- Selector: Emails ending in `@yourbusiness.com`

## Rollback

If issues arise, the app remains accessible via Tailscale at:
`http://mediastack-as.bone-egret.ts.net:8088`

To disable Cloudflare Tunnel:
```bash
pct exec 103 -- docker stop familyflix-cloudflared
```

To remove completely:
1. Remove cloudflared service from docker-compose
2. Delete tunnel in Cloudflare dashboard
3. Optionally revert nameservers to Squarespace

## Security Notes

- **No inbound ports:** Tunnel is outbound-only, no firewall changes needed
- **Zero Trust:** Every request authenticated before reaching your app
- **Encryption:** HTTPS from user → Cloudflare → tunnel → app
- **Audit logs:** Cloudflare logs all access attempts (Zero Trust → Logs)
- **Session management:** Can revoke sessions from dashboard if needed

## Cost Summary

| Item | Cost |
|------|------|
| Cloudflare account | Free |
| Zero Trust (up to 50 users) | Free |
| Tunnels | Free |
| andofam.com domain | Already owned |
| **Total** | **$0** |
