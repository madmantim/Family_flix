#!/bin/bash
# Family Flix Picker - Homelab Deployment Script
#
# Usage: ./deploy.sh [--first-run]
#   --first-run   Initial deployment (creates .env template, skips rebuild)
#
# Prerequisites:
#   - SSH access to pve-as (100.115.142.20 or pve-as.bone-egret.ts.net)
#   - .env file with API keys on target (after first run)
#
# Target: mediastack-as LXC (ID 103) at /opt/familyflix
# Access: http://mediastack-as.bone-egret.ts.net:8088

set -e

# Configuration
PROXMOX_HOST="100.115.142.20"
LXC_ID="103"
DEPLOY_PATH="/opt/familyflix"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[deploy]${NC} $1"; }
warn() { echo -e "${YELLOW}[warn]${NC} $1"; }
error() { echo -e "${RED}[error]${NC} $1"; exit 1; }

# Parse arguments
FIRST_RUN=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --first-run) FIRST_RUN=true ;;
        *) error "Unknown option: $1" ;;
    esac
    shift
done

# Helper to run commands on LXC via Proxmox
run_on_lxc() {
    ssh "root@${PROXMOX_HOST}" "pct exec ${LXC_ID} -- bash -c '$1'"
}

# Helper to copy files to LXC via Proxmox
copy_to_lxc() {
    local src="$1"
    local dest="$2"
    scp -r "$src" "root@${PROXMOX_HOST}:/tmp/familyflix-upload"
    ssh "root@${PROXMOX_HOST}" "pct push ${LXC_ID} /tmp/familyflix-upload ${dest}"
    ssh "root@${PROXMOX_HOST}" "rm -rf /tmp/familyflix-upload"
}

log "Starting deployment to mediastack-as LXC..."
log "Project root: ${PROJECT_ROOT}"

# Step 1: Create temp directory with files to deploy
log "Preparing deployment files..."
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

# Copy required directories
cp -r "${PROJECT_ROOT}/backend" "${TEMP_DIR}/"
cp -r "${PROJECT_ROOT}/frontend" "${TEMP_DIR}/"
cp "${PROJECT_ROOT}/deploy/docker-compose.homelab.yml" "${TEMP_DIR}/docker-compose.yml"

# Create .env.example for reference
cat > "${TEMP_DIR}/.env.example" << 'EOF'
# Family Flix Picker - Environment Variables
# Copy to .env and fill in your values: cp .env.example .env && chmod 600 .env

# TMDB API - Get from https://www.themoviedb.org/settings/api
TMDB_API_KEY=your_tmdb_api_key
TMDB_ACCESS_TOKEN=your_tmdb_access_token

# OMDb API - Get from https://www.omdbapi.com/apikey.aspx
OMDB_API_KEY=your_omdb_api_key
EOF

# Step 2: Sync to Proxmox host
log "Syncing files to Proxmox host..."
rsync -avz --delete \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'node_modules' \
    --exclude 'venv' \
    --exclude '.env' \
    --exclude '*.db' \
    --exclude 'dist' \
    "${TEMP_DIR}/" "root@${PROXMOX_HOST}:/tmp/familyflix-deploy/"

# Step 3: Copy to LXC container
log "Copying to LXC container ${LXC_ID}..."
ssh "root@${PROXMOX_HOST}" "pct exec ${LXC_ID} -- mkdir -p ${DEPLOY_PATH}"

# Use tar to preserve structure and avoid pct push limitations
ssh "root@${PROXMOX_HOST}" "cd /tmp/familyflix-deploy && tar czf /tmp/familyflix.tar.gz ."
ssh "root@${PROXMOX_HOST}" "pct push ${LXC_ID} /tmp/familyflix.tar.gz /tmp/familyflix.tar.gz"
ssh "root@${PROXMOX_HOST}" "pct exec ${LXC_ID} -- bash -c 'cd ${DEPLOY_PATH} && tar xzf /tmp/familyflix.tar.gz && rm /tmp/familyflix.tar.gz'"
ssh "root@${PROXMOX_HOST}" "rm -rf /tmp/familyflix.tar.gz /tmp/familyflix-deploy"

if $FIRST_RUN; then
    log "First run complete! Next steps:"
    echo ""
    echo "  1. SSH into the container and configure .env:"
    echo "     ssh root@${PROXMOX_HOST}"
    echo "     pct enter ${LXC_ID}"
    echo "     cd ${DEPLOY_PATH}"
    echo "     cp .env.example .env"
    echo "     nano .env  # Add your API keys"
    echo "     chmod 600 .env"
    echo ""
    echo "  2. Build and start the services:"
    echo "     docker compose up -d --build"
    echo ""
    echo "  3. Verify deployment:"
    echo "     docker ps"
    echo "     docker logs familyflix-backend"
    echo ""
    echo "  4. Access the app:"
    echo "     http://mediastack-as.bone-egret.ts.net:8088"
    echo ""
    exit 0
fi

# Step 4: Check if .env exists
log "Checking for .env file..."
if ! run_on_lxc "test -f ${DEPLOY_PATH}/.env"; then
    error ".env file not found! Run with --first-run first, then configure .env"
fi

# Step 5: Build and restart containers
log "Building and restarting containers..."
run_on_lxc "cd ${DEPLOY_PATH} && docker compose down --remove-orphans || true"
run_on_lxc "cd ${DEPLOY_PATH} && docker compose build --no-cache"
run_on_lxc "cd ${DEPLOY_PATH} && docker compose up -d"

# Step 6: Wait for health check
log "Waiting for backend health check..."
sleep 5
for i in {1..12}; do
    if run_on_lxc "docker exec familyflix-backend curl -sf http://localhost:8000/api/health" 2>/dev/null; then
        log "Backend is healthy!"
        break
    fi
    if [ $i -eq 12 ]; then
        warn "Health check timeout - check logs with: docker logs familyflix-backend"
    fi
    sleep 5
done

# Step 7: Show status
log "Deployment complete!"
echo ""
run_on_lxc "docker ps --filter name=familyflix"
echo ""
log "Access the app at: http://mediastack-as.bone-egret.ts.net:8088"
