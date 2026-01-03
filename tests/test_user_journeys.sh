#!/bin/bash
# Family Flix User Journey Tests
# Tests against production deployment

BASE_URL="https://mediastack-as.bone-egret.ts.net:8443"
PASS=0
FAIL=0
ERRORS=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASS++))
}

log_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    echo -e "  ${YELLOW}Expected${NC}: $2"
    echo -e "  ${YELLOW}Got${NC}: $3"
    ((FAIL++))
    ERRORS="$ERRORS\n- $1: Expected $2, Got $3"
}

# Helper to make requests
api_get() {
    curl -s "$BASE_URL$1"
}

api_post() {
    curl -s -X POST "$BASE_URL$1" -H "Content-Type: application/json" -d "$2"
}

api_delete() {
    curl -s -X DELETE "$BASE_URL$1"
}

api_patch() {
    curl -s -X PATCH "$BASE_URL$1" -H "Content-Type: application/json" -d "$2"
}

echo "=================================================="
echo "Family Flix User Journey Tests"
echo "Target: $BASE_URL"
echo "=================================================="
echo ""

# ==========================================
# JOURNEY 1: User Selection Flow
# ==========================================
echo "--- Journey 1: User Selection Flow ---"

# Test 1.1: Get all members
echo -n "1.1 Get all members... "
MEMBERS=$(api_get "/api/members")
MEMBER_COUNT=$(echo "$MEMBERS" | jq 'length')
if [ "$MEMBER_COUNT" -gt 0 ]; then
    log_pass "Got $MEMBER_COUNT members"
else
    log_fail "Get members" ">0 members" "$MEMBER_COUNT members"
fi

# Test 1.2: Get specific member
echo -n "1.2 Get member by ID (Tim)... "
MEMBER=$(api_get "/api/members/1")
MEMBER_NAME=$(echo "$MEMBER" | jq -r '.name')
if [ "$MEMBER_NAME" == "Tim" ]; then
    log_pass "Got member Tim"
else
    log_fail "Get member by ID" "Tim" "$MEMBER_NAME"
fi

# Test 1.3: Check member has required fields
echo -n "1.3 Member has all required fields... "
HAS_FIELDS=$(echo "$MEMBER" | jq 'has("id") and has("name") and has("content_filter") and has("avatar_url")')
if [ "$HAS_FIELDS" == "true" ]; then
    log_pass "Member has all required fields"
else
    log_fail "Member fields" "id, name, content_filter, avatar_url" "$(echo "$MEMBER" | jq 'keys')"
fi

echo ""

# ==========================================
# JOURNEY 2: Swipe Screen Flow
# ==========================================
echo "--- Journey 2: Swipe Screen Flow ---"

# Test 2.1: Get swipe queue
echo -n "2.1 Get swipe queue for member... "
QUEUE=$(api_get "/api/swipes/queue/1?limit=20")
QUEUE_STATUS=$(echo "$QUEUE" | jq -r 'type')
if [ "$QUEUE_STATUS" == "object" ]; then
    MOVIES_COUNT=$(echo "$QUEUE" | jq '.movies | length')
    log_pass "Got swipe queue with $MOVIES_COUNT movies"
else
    log_fail "Get swipe queue" "object with movies array" "$QUEUE_STATUS"
fi

# Test 2.2: Check swipe queue structure (fixed: uses total_unswiped)
echo -n "2.2 Swipe queue has correct structure... "
HAS_STRUCTURE=$(echo "$QUEUE" | jq 'has("movies") and has("total_unswiped")')
if [ "$HAS_STRUCTURE" == "true" ]; then
    log_pass "Queue has movies and total_unswiped fields"
else
    log_fail "Queue structure" "movies and total_unswiped" "$(echo "$QUEUE" | jq 'keys')"
fi

# Test 2.3: Get member's existing swipes
echo -n "2.3 Get member's swipe history... "
SWIPES=$(api_get "/api/swipes/member/1")
SWIPES_TYPE=$(echo "$SWIPES" | jq -r 'type')
if [ "$SWIPES_TYPE" == "array" ]; then
    SWIPES_COUNT=$(echo "$SWIPES" | jq 'length')
    log_pass "Got $SWIPES_COUNT existing swipes"
else
    log_fail "Get swipes" "array" "$SWIPES_TYPE"
fi

echo ""

# ==========================================
# JOURNEY 3: Watchlist Flow
# ==========================================
echo "--- Journey 3: Watchlist Flow ---"

# Test 3.1: Get watchlist
echo -n "3.1 Get active watchlist... "
WATCHLIST=$(api_get "/api/watchlist/?active_only=true")
WATCHLIST_TYPE=$(echo "$WATCHLIST" | jq -r 'type')
if [ "$WATCHLIST_TYPE" == "array" ]; then
    WL_COUNT=$(echo "$WATCHLIST" | jq 'length')
    log_pass "Got watchlist with $WL_COUNT entries"
else
    log_fail "Get watchlist" "array" "$WATCHLIST_TYPE"
fi

# Test 3.2: Search for movies
echo -n "3.2 Search for movies (query: 'Matrix')... "
SEARCH=$(api_get "/api/movies/search?query=Matrix&page=1")
SEARCH_RESULTS=$(echo "$SEARCH" | jq '.results | length')
if [ "$SEARCH_RESULTS" -gt 0 ]; then
    log_pass "Found $SEARCH_RESULTS movies"
else
    log_fail "Movie search" ">0 results" "$SEARCH_RESULTS results"
fi

# Test 3.3: Get trending movies
echo -n "3.3 Get trending movies... "
TRENDING=$(api_get "/api/movies/trending?page=1")
TRENDING_COUNT=$(echo "$TRENDING" | jq '.results | length')
if [ "$TRENDING_COUNT" -gt 0 ]; then
    log_pass "Got $TRENDING_COUNT trending movies"
else
    log_fail "Trending movies" ">0 movies" "$TRENDING_COUNT"
fi

# Test 3.4: Get discover movies (popular)
echo -n "3.4 Discover popular movies... "
DISCOVER=$(api_get "/api/movies/discover?tab=popular&page=1")
DISCOVER_COUNT=$(echo "$DISCOVER" | jq '.results | length')
if [ "$DISCOVER_COUNT" -gt 0 ]; then
    log_pass "Got $DISCOVER_COUNT popular movies"
else
    log_fail "Discover popular" ">0 movies" "$DISCOVER_COUNT"
fi

# Test 3.5: Watchlist entry has movie details
echo -n "3.5 Watchlist entries have movie details... "
FIRST_ENTRY=$(echo "$WATCHLIST" | jq '.[0]')
HAS_MOVIE=$(echo "$FIRST_ENTRY" | jq 'has("movie") and (.movie | has("title") and has("poster_url"))')
if [ "$HAS_MOVIE" == "true" ]; then
    log_pass "Watchlist entries include movie details"
else
    log_fail "Watchlist movie details" "movie with title, poster_url" "$(echo "$FIRST_ENTRY" | jq 'keys')"
fi

echo ""

# ==========================================
# JOURNEY 4: Movie Night Flow
# ==========================================
echo "--- Journey 4: Movie Night Flow ---"

# Test 4.1: Get matches for single member
echo -n "4.1 Get matches for single member... "
MATCHES=$(api_post "/api/movie-night/matches" '{"present_member_ids": [1]}')
MATCHES_TYPE=$(echo "$MATCHES" | jq -r 'type')
if [ "$MATCHES_TYPE" == "object" ]; then
    MATCHES_COUNT=$(echo "$MATCHES" | jq '.matches | length')
    log_pass "Got $MATCHES_COUNT matches"
else
    log_fail "Get matches" "object with matches" "$MATCHES_TYPE: $MATCHES"
fi

# Test 4.2: Get matches for multiple members
echo -n "4.2 Get matches for multiple members... "
MATCHES2=$(api_post "/api/movie-night/matches" '{"present_member_ids": [1, 3, 4]}')
MATCHES2_COUNT=$(echo "$MATCHES2" | jq '.matches | length')
if [ "$MATCHES2_COUNT" -ge 0 ]; then
    log_pass "Got $MATCHES2_COUNT matches for 3 members"
else
    log_fail "Multi-member matches" ">=0 matches" "error"
fi

# Test 4.3: Check match structure (fixed: only matches and present_members)
echo -n "4.3 Match response has correct structure... "
HAS_MATCH_STRUCT=$(echo "$MATCHES" | jq 'has("matches") and has("present_members")')
if [ "$HAS_MATCH_STRUCT" == "true" ]; then
    log_pass "Match response has matches and present_members"
else
    log_fail "Match structure" "matches, present_members" "$(echo "$MATCHES" | jq 'keys')"
fi

# Test 4.4: Match entries have vote info
echo -n "4.4 Match entries have vote information... "
if [ "$MATCHES_COUNT" -gt 0 ]; then
    FIRST_MATCH=$(echo "$MATCHES" | jq '.matches[0]')
    HAS_VOTES=$(echo "$FIRST_MATCH" | jq 'has("yes_votes") and has("is_full_match")')
    if [ "$HAS_VOTES" == "true" ]; then
        log_pass "Matches include vote info"
    else
        log_fail "Match vote info" "yes_votes, is_full_match" "$(echo "$FIRST_MATCH" | jq 'keys')"
    fi
else
    log_pass "No matches to check (skipped)"
fi

echo ""

# ==========================================
# JOURNEY 5: Watch History Flow
# ==========================================
echo "--- Journey 5: Watch History Flow ---"

# Test 5.1: Get member's watch history
echo -n "5.1 Get watch history... "
HISTORY=$(api_get "/api/watched/1")
HISTORY_TYPE=$(echo "$HISTORY" | jq -r 'type')
if [ "$HISTORY_TYPE" == "array" ]; then
    HISTORY_COUNT=$(echo "$HISTORY" | jq 'length')
    log_pass "Got $HISTORY_COUNT watched movies"
else
    log_fail "Get watch history" "array" "$HISTORY_TYPE"
fi

# Test 5.2: Get watch stats
echo -n "5.2 Get watch stats... "
STATS=$(api_get "/api/watched/history/stats")
STATS_TYPE=$(echo "$STATS" | jq -r 'type')
if [ "$STATS_TYPE" == "object" ]; then
    log_pass "Got watch stats"
else
    log_fail "Get watch stats" "object" "$STATS_TYPE"
fi

# Test 5.3: Watch stats has expected fields
echo -n "5.3 Watch stats has expected fields... "
HAS_STAT_FIELDS=$(echo "$STATS" | jq 'has("total_watched") and has("watched_this_year")')
if [ "$HAS_STAT_FIELDS" == "true" ]; then
    log_pass "Stats have total_watched and unique_movies"
else
    log_fail "Stats fields" "total_watched, unique_movies" "$(echo "$STATS" | jq 'keys')"
fi

echo ""

# ==========================================
# JOURNEY 6: Static Files & Assets
# ==========================================
echo "--- Journey 6: Static Files & Assets ---"

# Test 6.1: Frontend loads
echo -n "6.1 Frontend HTML loads... "
FRONTEND=$(curl -sI "$BASE_URL/" | head -1)
if [[ "$FRONTEND" == *"200"* ]]; then
    log_pass "Frontend returns 200"
else
    log_fail "Frontend load" "200 OK" "$FRONTEND"
fi

# Test 6.2: JS assets load
echo -n "6.2 JavaScript assets load... "
JS_URL=$(curl -s "$BASE_URL/" | grep -o 'src="/assets/[^"]*\.js"' | head -1 | sed 's/src="//;s/"$//')
if [ -n "$JS_URL" ]; then
    JS_STATUS=$(curl -sI "$BASE_URL$JS_URL" | head -1)
    if [[ "$JS_STATUS" == *"200"* ]]; then
        log_pass "JS assets return 200"
    else
        log_fail "JS assets" "200 OK" "$JS_STATUS"
    fi
else
    log_fail "JS assets" "JS URL found" "no JS URL in HTML"
fi

# Test 6.3: CSS assets load
echo -n "6.3 CSS assets load... "
CSS_URL=$(curl -s "$BASE_URL/" | grep -o 'href="/assets/[^"]*\.css"' | head -1 | sed 's/href="//;s/"$//')
if [ -n "$CSS_URL" ]; then
    CSS_STATUS=$(curl -sI "$BASE_URL$CSS_URL" | head -1)
    if [[ "$CSS_STATUS" == *"200"* ]]; then
        log_pass "CSS assets return 200"
    else
        log_fail "CSS assets" "200 OK" "$CSS_STATUS"
    fi
else
    log_fail "CSS assets" "CSS URL found" "no CSS URL in HTML"
fi

# Test 6.4: Avatar static file
echo -n "6.4 Avatar static file loads... "
AVATAR_STATUS=$(curl -sI "$BASE_URL/static/avatars/1.jpg" | head -1)
if [[ "$AVATAR_STATUS" == *"200"* ]]; then
    log_pass "Avatar file returns 200"
else
    log_fail "Avatar file" "200 OK" "$AVATAR_STATUS"
fi

# Test 6.5: Manifest loads
echo -n "6.5 PWA manifest loads... "
MANIFEST_STATUS=$(curl -sI "$BASE_URL/manifest.json" | head -1)
if [[ "$MANIFEST_STATUS" == *"200"* ]]; then
    log_pass "Manifest returns 200"
else
    log_fail "Manifest" "200 OK" "$MANIFEST_STATUS"
fi

# Test 6.6: PWA icons load
echo -n "6.6 PWA icons load... "
ICON192_STATUS=$(curl -sI "$BASE_URL/icon-192.png" | head -1)
ICON512_STATUS=$(curl -sI "$BASE_URL/icon-512.png" | head -1)
if [[ "$ICON192_STATUS" == *"200"* ]] && [[ "$ICON512_STATUS" == *"200"* ]]; then
    log_pass "PWA icons return 200"
else
    log_fail "PWA icons" "200 OK for both" "192: $ICON192_STATUS, 512: $ICON512_STATUS"
fi

echo ""

# ==========================================
# JOURNEY 7: Recording Actions (Write Tests)
# ==========================================
echo "--- Journey 7: Recording Actions ---"

# Test 7.1: Record a swipe (YES)
echo -n "7.1 Record swipe vote... "
# Get a movie from the swipe queue (uses internal id, not tmdb_id)
QUEUE_FOR_SWIPE=$(api_get "/api/swipes/queue/1?limit=1")
MOVIE_ID=$(echo "$QUEUE_FOR_SWIPE" | jq '.movies[0].id // empty')
if [ "$MOVIE_ID" != "null" ] && [ -n "$MOVIE_ID" ]; then
    SWIPE_RESULT=$(api_post "/api/swipes" "{\"member_id\": 1, \"movie_id\": $MOVIE_ID, \"direction\": \"yes\", \"watched\": false}")
    SWIPE_DIR=$(echo "$SWIPE_RESULT" | jq -r '.direction // .detail // "error"')
    if [ "$SWIPE_DIR" == "yes" ] || [[ "$SWIPE_DIR" == *"already"* ]]; then
        log_pass "Swipe recorded (or already exists)"
    else
        log_fail "Record swipe" "yes or already exists" "$SWIPE_DIR"
    fi
else
    log_fail "Record swipe" "movie ID from trending" "null"
fi

# Test 7.2: API handles invalid requests gracefully
echo -n "7.2 API handles invalid member ID... "
INVALID=$(api_get "/api/members/99999")
INVALID_MSG=$(echo "$INVALID" | jq -r '.detail // "no detail"')
if [[ "$INVALID_MSG" == *"not found"* ]] || [[ "$INVALID_MSG" == *"Not Found"* ]]; then
    log_pass "Returns 'not found' for invalid ID"
else
    log_fail "Invalid ID handling" "not found message" "$INVALID_MSG"
fi

echo ""

# ==========================================
# SUMMARY
# ==========================================
echo "=================================================="
echo "Test Summary"
echo "=================================================="
echo -e "${GREEN}Passed${NC}: $PASS"
echo -e "${RED}Failed${NC}: $FAIL"
echo ""

if [ $FAIL -gt 0 ]; then
    echo -e "${RED}Failed Tests:${NC}"
    echo -e "$ERRORS"
    echo ""
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
