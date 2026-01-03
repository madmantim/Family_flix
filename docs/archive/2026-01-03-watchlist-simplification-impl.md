# Watchlist Simplification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Simplify watchlist logic so Y vote = "want to watch" and remove the confusing would_rewatch flag.

**Architecture:** Remove would_rewatch from schema, update Movie Night ranking to use Y-count + N(W)-count + recency, update frontend to filter by Y votes and remove watched toggle.

**Tech Stack:** Python/FastAPI, SQLAlchemy, React/TypeScript, TanStack Query

---

## Task 1: Remove would_rewatch from Backend Model

**Files:**
- Modify: `backend/app/models.py:100-115`

**Step 1: Remove the would_rewatch column**

```python
class MemberWatched(Base):
    """Per-member watched status for movies"""
    __tablename__ = "member_watched"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    watched_at = Column(DateTime, default=datetime.utcnow)
    # REMOVED: would_rewatch = Column(Boolean, default=False)

    member = relationship("Member", back_populates="watched_movies")
    movie = relationship("Movie", back_populates="member_watched")

    __table_args__ = (
        UniqueConstraint('member_id', 'movie_id', name='unique_member_movie_watched'),
    )
```

**Step 2: Commit**

```bash
git add backend/app/models.py
git commit -m "refactor: remove would_rewatch from MemberWatched model"
```

---

## Task 2: Update Backend Schemas

**Files:**
- Modify: `backend/app/schemas.py:140-174`

**Step 1: Remove would_rewatch from all schemas**

```python
# Member Watched schemas
class MemberWatchedCreate(BaseModel):
    member_id: int
    movie_id: int


class MemberWatchedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    movie_id: int
    watched_at: datetime


class MemberWatchedWithMovie(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie: MovieResponse
    watched_at: datetime


class MarkWatchedRequest(BaseModel):
    movie_id: int
    member_ids: List[int]
```

**Step 2: Remove MemberWatchedUpdate schema entirely**

Delete lines 147-148:
```python
# DELETE THIS:
# class MemberWatchedUpdate(BaseModel):
#     would_rewatch: bool
```

**Step 3: Commit**

```bash
git add backend/app/schemas.py
git commit -m "refactor: remove would_rewatch from schemas"
```

---

## Task 3: Update watched.py - Remove would_rewatch Logic

**Files:**
- Modify: `backend/app/routers/watched.py`

**Step 1: Update mark_watched endpoint (lines 117-164)**

Remove would_rewatch handling and the is_active side effect. Add swipe flip to N:

```python
@router.post("/", response_model=List[MemberWatchedResponse])
def mark_watched(request: MarkWatchedRequest, db: Session = Depends(get_db)):
    """Mark a movie as watched for multiple members and flip their votes to N"""
    # Validate movie exists
    movie = db.query(Movie).filter(Movie.id == request.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Validate all members exist
    members = db.query(Member).filter(Member.id.in_(request.member_ids)).all()
    if len(members) != len(request.member_ids):
        raise HTTPException(status_code=404, detail="One or more members not found")

    # NOTE: We no longer deactivate watchlist entries here
    # Pool membership is independent of watched state

    results = []
    for member_id in request.member_ids:
        # Create or update watched record
        existing = db.query(MemberWatched).filter(
            MemberWatched.member_id == member_id,
            MemberWatched.movie_id == request.movie_id
        ).first()

        if existing:
            # Already watched, just return it
            results.append(existing)
        else:
            # Create new record
            watched = MemberWatched(
                member_id=member_id,
                movie_id=request.movie_id
            )
            db.add(watched)
            db.commit()
            db.refresh(watched)
            results.append(watched)

        # Flip swipe to NO for this member (they just watched it)
        existing_swipe = db.query(Swipe).filter(
            Swipe.member_id == member_id,
            Swipe.movie_id == request.movie_id
        ).first()

        if existing_swipe:
            existing_swipe.direction = SwipeDirection.NO
            db.commit()
        else:
            # Create NO swipe if none exists
            new_swipe = Swipe(
                member_id=member_id,
                movie_id=request.movie_id,
                direction=SwipeDirection.NO
            )
            db.add(new_swipe)
            db.commit()

    return results
```

**Step 2: Add Swipe import at top of file**

```python
from ..models import MemberWatched, Member, Movie, WatchlistEntry, Swipe, SwipeDirection
```

**Step 3: Update get_member_watched to remove would_rewatch from response (lines 167-213)**

```python
@router.get("/{member_id}", response_model=List[MemberWatchedWithMovie])
def get_member_watched(member_id: int, limit: int = None, db: Session = Depends(get_db)):
    """Get all movies a member has watched"""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    query = db.query(MemberWatched).filter(
        MemberWatched.member_id == member_id
    ).order_by(MemberWatched.watched_at.desc())

    if limit:
        query = query.limit(limit)

    watched = query.all()

    result = []
    for w in watched:
        movie = w.movie
        result.append({
            "id": w.id,
            "movie": {
                "id": movie.id,
                "tmdb_id": movie.tmdb_id,
                "title": movie.title,
                "year": movie.year,
                "overview": movie.overview,
                "poster_path": movie.poster_path,
                "backdrop_path": movie.backdrop_path,
                "vote_average": movie.vote_average,
                "content_rating": movie.content_rating,
                "runtime": movie.runtime,
                "genres": movie.genres,
                "imdb_id": movie.imdb_id,
                "rt_critic_score": movie.rt_critic_score,
                "rt_audience_score": movie.rt_audience_score,
                "rt_url": movie.rt_url,
                "trailer_url": movie.trailer_url,
                "created_at": movie.created_at,
                "poster_url": TMDBService.get_poster_url(movie.poster_path),
                "backdrop_url": TMDBService.get_backdrop_url(movie.backdrop_path),
            },
            "watched_at": w.watched_at,
        })

    return result
```

**Step 4: Remove update_would_rewatch endpoint entirely (lines 216-236)**

Delete the entire `@router.patch("/{member_id}/{movie_id}")` function.

**Step 5: Update toggle_watched to remove would_rewatch (lines 239-273)**

```python
@router.put("/{member_id}/{movie_id}", response_model=MemberWatchedResponse)
def toggle_watched(member_id: int, movie_id: int, db: Session = Depends(get_db)):
    """
    Simple watched toggle - marks movie as watched for a member.
    No side effects (doesn't affect watchlist or swipes).
    Use DELETE to unmark.
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Check if already watched
    existing = db.query(MemberWatched).filter(
        MemberWatched.member_id == member_id,
        MemberWatched.movie_id == movie_id
    ).first()

    if existing:
        return existing

    # Create new watched record (no side effects)
    watched = MemberWatched(
        member_id=member_id,
        movie_id=movie_id
    )
    db.add(watched)
    db.commit()
    db.refresh(watched)

    return watched
```

**Step 6: Update get_all_watched_history response (lines 23-84)**

Remove would_rewatch from the response dict (line 81).

**Step 7: Commit**

```bash
git add backend/app/routers/watched.py
git commit -m "refactor: remove would_rewatch from watched router, add swipe flip"
```

---

## Task 4: Update Movie Night Algorithm

**Files:**
- Modify: `backend/app/routers/movie_night.py`

**Step 1: Rewrite the matching algorithm**

Replace the entire `get_matches` function:

```python
@router.post("/matches", response_model=MovieNightResponse)
def get_matches(request: MovieNightRequest, db: Session = Depends(get_db)):
    """
    Calculate movie matches for present members.

    Ranking (simplified):
    1. Y count (descending) - more yes votes = better
    2. N(W) count (ascending) - fewer watched among N voters = fresher
    3. Recency (newest first) - tiebreaker
    """
    if len(request.present_member_ids) < 1:
        raise HTTPException(status_code=400, detail="At least one member must be present")

    # Validate all members exist
    members = db.query(Member).filter(Member.id.in_(request.present_member_ids)).all()
    if len(members) != len(request.present_member_ids):
        raise HTTPException(status_code=404, detail="One or more members not found")

    member_ids = request.present_member_ids
    members_by_id = {m.id: m for m in members}

    # Determine the most restrictive content filter for present members
    content_filters = [m.content_filter for m in members]
    filter_order = [ContentRating.ALL_AGES, ContentRating.TEEN, ContentRating.MATURE, ContentRating.ADULT]
    min_filter = min(content_filters, key=lambda x: filter_order.index(x))

    # Get all active watchlist movies
    active_movies = db.query(Movie).join(WatchlistEntry).filter(
        WatchlistEntry.is_active == True
    ).all()

    # Filter by content rating
    allowed_ratings = filter_order[:filter_order.index(min_filter) + 1]
    filtered_movies = [m for m in active_movies if m.content_rating in allowed_ratings]

    matches = []

    for movie in filtered_movies:
        # Get yes swipes from present members
        yes_swipes = db.query(Swipe).filter(
            Swipe.movie_id == movie.id,
            Swipe.member_id.in_(member_ids),
            Swipe.direction == SwipeDirection.YES
        ).all()

        yes_member_ids = {s.member_id for s in yes_swipes}
        yes_voters = [members_by_id[mid] for mid in yes_member_ids if mid in members_by_id]
        y_count = len(yes_member_ids)

        # Count N(W) - members who voted NO (or didn't vote YES) AND have watched
        n_watched_count = 0
        for mid in member_ids:
            if mid not in yes_member_ids:
                # This member didn't vote YES - check if they've watched
                watched = db.query(MemberWatched).filter(
                    MemberWatched.member_id == mid,
                    MemberWatched.movie_id == movie.id
                ).first()
                if watched:
                    n_watched_count += 1

        # Get watchlist entry for recency
        entry = db.query(WatchlistEntry).filter(
            WatchlistEntry.movie_id == movie.id,
            WatchlistEntry.is_active == True
        ).first()

        matches.append({
            "movie": movie,
            "yes_votes": y_count,
            "total_present": len(member_ids),
            "is_full_match": y_count == len(member_ids),
            "n_watched_count": n_watched_count,
            "added_at": entry.added_at if entry else None,
            "voters": yes_voters
        })

    # Sort: Y count desc, N(W) count asc, recency desc
    matches.sort(key=lambda m: (
        -m["yes_votes"],
        m["n_watched_count"],
        -(m["added_at"].timestamp() if m["added_at"] else 0)
    ))

    result = []
    for m in matches:
        movie = m["movie"]
        result.append(MatchedMovie(
            movie={
                "id": movie.id,
                "tmdb_id": movie.tmdb_id,
                "title": movie.title,
                "year": movie.year,
                "overview": movie.overview,
                "poster_path": movie.poster_path,
                "backdrop_path": movie.backdrop_path,
                "vote_average": movie.vote_average,
                "content_rating": movie.content_rating,
                "runtime": movie.runtime,
                "genres": movie.genres,
                "imdb_id": movie.imdb_id,
                "rt_critic_score": movie.rt_critic_score,
                "rt_audience_score": movie.rt_audience_score,
                "rt_url": movie.rt_url,
                "trailer_url": movie.trailer_url,
                "created_at": movie.created_at,
                "poster_url": TMDBService.get_poster_url(movie.poster_path),
                "backdrop_url": TMDBService.get_backdrop_url(movie.backdrop_path)
            },
            yes_votes=m["yes_votes"],
            total_present=m["total_present"],
            is_full_match=m["is_full_match"],
            voters=[{
                "id": v.id,
                "name": v.name,
                "avatar_url": v.avatar_url,
                "content_filter": v.content_filter,
                "created_at": v.created_at
            } for v in m["voters"]]
        ))

    return MovieNightResponse(
        matches=result,
        present_members=members
    )
```

**Step 2: Commit**

```bash
git add backend/app/routers/movie_night.py
git commit -m "refactor: simplify Movie Night ranking to Y-count, N(W)-count, recency"
```

---

## Task 5: Update Frontend Types

**Files:**
- Modify: `frontend/src/types/index.ts:51-56`

**Step 1: Remove would_rewatch from MemberWatched**

```typescript
export interface MemberWatched {
  id: number;
  movie: Movie;
  watched_at: string;
}
```

**Step 2: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "refactor: remove would_rewatch from frontend types"
```

---

## Task 6: Update Frontend API Client

**Files:**
- Modify: `frontend/src/api/client.ts:79-83`

**Step 1: Remove would_rewatch from markMovieWatched**

```typescript
export const markMovieWatched = (movieId: number, memberIds: number[]) =>
  api.post('/watched/', { movie_id: movieId, member_ids: memberIds }).then(r => r.data);
```

**Step 2: Remove updateWouldRewatch function entirely**

Delete lines 82-83:
```typescript
// DELETE:
// export const updateWouldRewatch = (memberId: number, movieId: number, wouldRewatch: boolean) =>
//   api.patch(`/watched/${memberId}/${movieId}`, { would_rewatch: wouldRewatch }).then(r => r.data);
```

**Step 3: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "refactor: remove would_rewatch from API client"
```

---

## Task 7: Update Watchlist Page - Remove Toggle and Update Filtering

**Files:**
- Modify: `frontend/src/pages/Watchlist.tsx`

**Step 1: Remove showWatched state and watched view logic**

Remove:
- `const [showWatched, setShowWatched] = useState(false);`
- The watched toggle button in header
- The `showWatched ? (...)` conditional rendering
- The `updateRewatchMutation`

**Step 2: Update filtering to show Y-voted movies**

Replace the current filter logic (lines 213-221) with:

```typescript
.filter((entry) => {
  // Show movies where the current member has voted YES
  const memberSwipe = memberSwipes?.find(s => s.movie_id === entry.movie.id);
  return memberSwipe?.direction === 'yes';
})
```

**Step 3: Remove would_rewatch related imports**

Remove `updateWouldRewatch` from imports.

**Step 4: Full updated component**

The key changes:
1. Remove `showWatched` state
2. Remove toggle button from header
3. Remove `updateRewatchMutation`
4. Update filter to use swipe direction
5. Remove watched list view

**Step 5: Commit**

```bash
git add frontend/src/pages/Watchlist.tsx
git commit -m "refactor: remove watched toggle, filter watchlist by Y votes"
```

---

## Task 8: Update Watchlist CSS - Remove Watched Styles

**Files:**
- Modify: `frontend/src/pages/Watchlist.css`

**Step 1: Remove watched-related styles**

Remove any `.watched-toggle-btn`, `.watched-list`, `.watched-item`, `.rewatch-btn` styles.

**Step 2: Commit**

```bash
git add frontend/src/pages/Watchlist.css
git commit -m "refactor: remove watched toggle styles from Watchlist"
```

---

## Task 9: Add "Want to Watch Again" to History Page

**Files:**
- Modify: `frontend/src/pages/History.tsx`
- Modify: `frontend/src/pages/History.css`

**Step 1: Add recordSwipe import and mutation**

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { getWatchHistory, getWatchStats, recordSwipe, getMemberSwipes } from '../api/client';
```

**Step 2: Add swipes query and mutation**

```typescript
const queryClient = useQueryClient();

const { data: memberSwipes } = useQuery({
  queryKey: ['memberSwipes', memberId],
  queryFn: () => getMemberSwipes(memberId!),
  enabled: !!memberId,
});

const rewatchMutation = useMutation({
  mutationFn: (movieId: number) => recordSwipe(memberId!, movieId, 'yes'),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['memberSwipes', memberId] });
  },
});
```

**Step 3: Add rewatch button to history items**

```typescript
{history?.map((entry, i) => {
  const hasYesVote = memberSwipes?.some(
    s => s.movie_id === entry.movie.id && s.direction === 'yes'
  );

  return (
    <motion.div
      key={entry.id}
      className="history-item"
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: i * 0.05 }}
    >
      <div
        className="poster"
        style={{
          backgroundImage: entry.movie.poster_url
            ? `url(${entry.movie.poster_url})`
            : undefined,
        }}
      />
      <div className="info">
        <h3>{entry.movie.title}</h3>
        <span className="date">{formatDate(entry.watched_at)}</span>
      </div>
      <button
        className={`rewatch-btn ${hasYesVote ? 'active' : ''}`}
        onClick={() => rewatchMutation.mutate(entry.movie.id)}
        disabled={rewatchMutation.isPending || hasYesVote}
        title={hasYesVote ? 'On your watchlist' : 'Want to watch again'}
      >
        {hasYesVote ? '♥' : '♡'}
      </button>
    </motion.div>
  );
})}
```

**Step 4: Add CSS for rewatch button**

Add to History.css:

```css
.history-item .rewatch-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  color: #666;
  transition: color 0.2s, transform 0.2s;
}

.history-item .rewatch-btn:hover:not(:disabled) {
  transform: scale(1.1);
}

.history-item .rewatch-btn.active {
  color: #e91e63;
}

.history-item .rewatch-btn:disabled {
  opacity: 0.5;
  cursor: default;
}
```

**Step 5: Commit**

```bash
git add frontend/src/pages/History.tsx frontend/src/pages/History.css
git commit -m "feat: add 'want to watch again' button to History page"
```

---

## Task 10: Clean Up MovieDetailCard

**Files:**
- Modify: `frontend/src/components/MovieDetailCard.tsx`

**Step 1: Review and remove any would_rewatch references**

Check if there are any would_rewatch related props or logic and remove them.

**Step 2: Commit (if changes needed)**

```bash
git add frontend/src/components/MovieDetailCard.tsx
git commit -m "refactor: clean up MovieDetailCard, remove would_rewatch"
```

---

## Task 11: Delete Database and Test

**Step 1: Delete the SQLite database to start fresh**

```bash
rm backend/family_flix.db
```

**Step 2: Start the backend to recreate the database**

```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Step 3: Test the frontend**

```bash
cd frontend && npm run dev
```

**Step 4: Manual testing checklist**

- [ ] Create a member
- [ ] Add movies to pool via search/discover
- [ ] Swipe YES on some movies
- [ ] Verify Watchlist only shows Y-voted movies
- [ ] Start Movie Night, select members, verify ranking
- [ ] Mark a movie as watched
- [ ] Verify swipe flipped to N and movie left personal watchlist
- [ ] Go to History, verify "want to watch again" button works
- [ ] Click heart, verify movie reappears on watchlist

**Step 5: Final commit**

```bash
git add -A
git commit -m "chore: complete watchlist simplification implementation"
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Remove would_rewatch from model |
| 2 | Update schemas |
| 3 | Update watched router (remove would_rewatch, add swipe flip) |
| 4 | Update Movie Night algorithm |
| 5 | Update frontend types |
| 6 | Update API client |
| 7 | Update Watchlist page |
| 8 | Clean up Watchlist CSS |
| 9 | Add rewatch button to History |
| 10 | Clean up MovieDetailCard |
| 11 | Test everything |
