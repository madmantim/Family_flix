# Per-Member Watched Tracking Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Track which family members have watched each movie, allowing movies to remain available for those who haven't seen them.

**Architecture:** New `member_watched` table with per-member watched status and would_rewatch flag. Swipe screen gets watched toggle. Movie Night matching filters by watched status. Watchlist gets toggle to show personal watched list.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, React, TypeScript, TanStack Query

---

## Task 1: Database Model

**Files:**
- Modify: `backend/app/models.py`

**Step 1: Add MemberWatched model to models.py**

Add after the `Swipe` class (around line 97):

```python
class MemberWatched(Base):
    """Per-member watched status for movies"""
    __tablename__ = "member_watched"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    watched_at = Column(DateTime, default=datetime.utcnow)
    would_rewatch = Column(Boolean, default=False)

    member = relationship("Member", back_populates="watched_movies")
    movie = relationship("Movie", back_populates="member_watched")

    __table_args__ = (
        UniqueConstraint('member_id', 'movie_id', name='unique_member_movie_watched'),
    )
```

**Step 2: Add import for UniqueConstraint**

At top of file, update the import:

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
```

**Step 3: Add relationships to Member class**

Add to `Member` class (around line 33):

```python
    watched_movies = relationship("MemberWatched", back_populates="member")
```

**Step 4: Add relationship to Movie class**

Add to `Movie` class (around line 61):

```python
    member_watched = relationship("MemberWatched", back_populates="movie")
```

**Step 5: Run database migration**

```bash
cd backend
source venv/bin/activate
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
```

**Step 6: Verify table created**

```bash
sqlite3 family_flix.db ".schema member_watched"
```

Expected: Table schema with id, member_id, movie_id, watched_at, would_rewatch columns.

**Step 7: Commit**

```bash
git add backend/app/models.py
git commit -m "feat: add MemberWatched model for per-member watched tracking"
```

---

## Task 2: Pydantic Schemas

**Files:**
- Modify: `backend/app/schemas.py`

**Step 1: Add MemberWatched schemas**

Add after `WatchHistoryResponse` class (around line 139):

```python
# Member Watched schemas
class MemberWatchedCreate(BaseModel):
    member_id: int
    movie_id: int
    would_rewatch: bool = False


class MemberWatchedUpdate(BaseModel):
    would_rewatch: bool


class MemberWatchedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    movie_id: int
    watched_at: datetime
    would_rewatch: bool


class MemberWatchedWithMovie(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie: MovieResponse
    watched_at: datetime
    would_rewatch: bool


class MarkWatchedRequest(BaseModel):
    movie_id: int
    member_ids: List[int]
    would_rewatch: bool = False
```

**Step 2: Update SwipeCreate to include watched flag**

Modify the existing `SwipeCreate` class:

```python
class SwipeCreate(BaseModel):
    member_id: int
    movie_id: int
    direction: SwipeDirection
    watched: bool = False  # New field
```

**Step 3: Commit**

```bash
git add backend/app/schemas.py
git commit -m "feat: add MemberWatched schemas and watched flag to SwipeCreate"
```

---

## Task 3: Watched Router (Backend API)

**Files:**
- Create: `backend/app/routers/watched.py`
- Modify: `backend/app/main.py`

**Step 1: Create watched router**

Create new file `backend/app/routers/watched.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import MemberWatched, Member, Movie
from ..schemas import (
    MemberWatchedCreate,
    MemberWatchedUpdate,
    MemberWatchedResponse,
    MemberWatchedWithMovie,
    MarkWatchedRequest,
    MovieResponse,
)
from ..services.tmdb import TMDBService

router = APIRouter()


@router.get("/{member_id}", response_model=List[MemberWatchedWithMovie])
def get_member_watched(member_id: int, db: Session = Depends(get_db)):
    """Get all movies a member has watched"""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    watched = db.query(MemberWatched).filter(
        MemberWatched.member_id == member_id
    ).order_by(MemberWatched.watched_at.desc()).all()

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
            "would_rewatch": w.would_rewatch,
        })

    return result


@router.post("/", response_model=List[MemberWatchedResponse])
def mark_watched(request: MarkWatchedRequest, db: Session = Depends(get_db)):
    """Mark a movie as watched for multiple members"""
    # Validate movie exists
    movie = db.query(Movie).filter(Movie.id == request.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Validate all members exist
    members = db.query(Member).filter(Member.id.in_(request.member_ids)).all()
    if len(members) != len(request.member_ids):
        raise HTTPException(status_code=404, detail="One or more members not found")

    results = []
    for member_id in request.member_ids:
        # Check if already watched
        existing = db.query(MemberWatched).filter(
            MemberWatched.member_id == member_id,
            MemberWatched.movie_id == request.movie_id
        ).first()

        if existing:
            # Update would_rewatch if already exists
            existing.would_rewatch = request.would_rewatch
            db.commit()
            db.refresh(existing)
            results.append(existing)
        else:
            # Create new record
            watched = MemberWatched(
                member_id=member_id,
                movie_id=request.movie_id,
                would_rewatch=request.would_rewatch
            )
            db.add(watched)
            db.commit()
            db.refresh(watched)
            results.append(watched)

    return results


@router.patch("/{member_id}/{movie_id}", response_model=MemberWatchedResponse)
def update_would_rewatch(
    member_id: int,
    movie_id: int,
    update: MemberWatchedUpdate,
    db: Session = Depends(get_db)
):
    """Update would_rewatch status for a member's watched movie"""
    watched = db.query(MemberWatched).filter(
        MemberWatched.member_id == member_id,
        MemberWatched.movie_id == movie_id
    ).first()

    if not watched:
        raise HTTPException(status_code=404, detail="Watched record not found")

    watched.would_rewatch = update.would_rewatch
    db.commit()
    db.refresh(watched)

    return watched


@router.delete("/{member_id}/{movie_id}", status_code=204)
def remove_watched(member_id: int, movie_id: int, db: Session = Depends(get_db)):
    """Remove watched status for a member (rarely used)"""
    watched = db.query(MemberWatched).filter(
        MemberWatched.member_id == member_id,
        MemberWatched.movie_id == movie_id
    ).first()

    if not watched:
        raise HTTPException(status_code=404, detail="Watched record not found")

    db.delete(watched)
    db.commit()
```

**Step 2: Register router in main.py**

In `backend/app/main.py`, add import and include router:

```python
from .routers import members, movies, swipes, watchlist, movie_night, history, watched
```

And add:

```python
app.include_router(watched.router, prefix="/api/watched", tags=["watched"])
```

**Step 3: Test the endpoints manually**

```bash
# Restart server
pkill -f "uvicorn app.main:app" || true
cd backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 &
sleep 3

# Test get watched (should be empty)
curl -s http://localhost:8000/api/watched/1 | python3 -m json.tool

# Test mark watched
curl -s -X POST http://localhost:8000/api/watched/ \
  -H "Content-Type: application/json" \
  -d '{"movie_id": 1, "member_ids": [1], "would_rewatch": false}'
```

**Step 4: Commit**

```bash
git add backend/app/routers/watched.py backend/app/main.py
git commit -m "feat: add watched router with CRUD endpoints"
```

---

## Task 4: Update Swipes Router

**Files:**
- Modify: `backend/app/routers/swipes.py`

**Step 1: Import MemberWatched model**

Add to imports:

```python
from ..models import Movie, Member, Swipe, WatchlistEntry, SwipeDirection, ContentRating, MemberWatched
```

**Step 2: Update create_swipe to handle watched flag**

Modify the `create_swipe` function to create MemberWatched record when watched=True:

```python
@router.post("/", response_model=SwipeResponse, status_code=201)
def create_swipe(swipe: SwipeCreate, db: Session = Depends(get_db)):
    """Record a swipe vote"""
    # Validate member
    member = db.query(Member).filter(Member.id == swipe.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Validate movie
    movie = db.query(Movie).filter(Movie.id == swipe.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Check for existing swipe
    existing = db.query(Swipe).filter(
        Swipe.member_id == swipe.member_id,
        Swipe.movie_id == swipe.movie_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already swiped on this movie")

    # Create swipe
    db_swipe = Swipe(
        member_id=swipe.member_id,
        movie_id=swipe.movie_id,
        direction=swipe.direction
    )
    db.add(db_swipe)

    # If watched flag is set, create/update MemberWatched record
    if swipe.watched:
        would_rewatch = swipe.direction == SwipeDirection.YES
        existing_watched = db.query(MemberWatched).filter(
            MemberWatched.member_id == swipe.member_id,
            MemberWatched.movie_id == swipe.movie_id
        ).first()

        if existing_watched:
            existing_watched.would_rewatch = would_rewatch
        else:
            watched_record = MemberWatched(
                member_id=swipe.member_id,
                movie_id=swipe.movie_id,
                would_rewatch=would_rewatch
            )
            db.add(watched_record)

    db.commit()
    db.refresh(db_swipe)

    return db_swipe
```

**Step 3: Commit**

```bash
git add backend/app/routers/swipes.py
git commit -m "feat: swipes router creates MemberWatched when watched flag set"
```

---

## Task 5: Update Movie Night Matching

**Files:**
- Modify: `backend/app/routers/movie_night.py`

**Step 1: Import MemberWatched model**

Add to imports:

```python
from ..models import Movie, Member, Swipe, WatchlistEntry, SwipeDirection, ContentRating, MemberWatched
```

**Step 2: Update get_matches to filter by watched status**

Replace the matching logic in `get_matches` function. The key change is adding eligibility check:

Find this section (around line 54-78):

```python
    # Calculate yes votes for each movie from present members
    matches = []

    for movie in filtered_movies:
```

Replace the entire for loop with:

```python
    # Calculate yes votes for each movie from present members
    matches = []

    for movie in filtered_movies:
        # Get yes swipes from present members
        yes_swipes = db.query(Swipe).filter(
            Swipe.movie_id == movie.id,
            Swipe.member_id.in_(member_ids),
            Swipe.direction == SwipeDirection.YES
        ).all()

        yes_member_ids = {s.member_id for s in yes_swipes}

        # Check eligibility: member is eligible if not watched OR would_rewatch=True
        eligible_count = 0
        for mid in member_ids:
            watched = db.query(MemberWatched).filter(
                MemberWatched.member_id == mid,
                MemberWatched.movie_id == movie.id
            ).first()

            if watched is None:
                # Not watched = eligible (if they swiped yes)
                if mid in yes_member_ids:
                    eligible_count += 1
            elif watched.would_rewatch:
                # Watched but would rewatch = eligible (if they swiped yes)
                if mid in yes_member_ids:
                    eligible_count += 1
            # else: watched and would not rewatch = not eligible

        # Only include if all present members are eligible and swiped yes
        # A member must have swiped yes AND be eligible (not watched or would_rewatch)
        all_eligible = eligible_count == len(member_ids)

        if eligible_count == 0:
            continue  # Skip movies with no eligible members

        # Get watchlist entry for source info
        entry = db.query(WatchlistEntry).filter(
            WatchlistEntry.movie_id == movie.id,
            WatchlistEntry.is_active == True
        ).first()

        matches.append({
            "movie": movie,
            "yes_votes": eligible_count,
            "total_present": len(member_ids),
            "is_full_match": all_eligible,
            "source": entry.source if entry else "manual",
            "added_at": entry.added_at if entry else None
        })
```

**Step 3: Commit**

```bash
git add backend/app/routers/movie_night.py
git commit -m "feat: movie night matching filters by watched status"
```

---

## Task 6: Backend Tests

**Files:**
- Create: `backend/tests/test_member_watched.py`

**Step 1: Create test file**

```python
"""Tests for per-member watched tracking feature"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import Member, Movie, Swipe, MemberWatched, SwipeDirection, ContentRating, WatchlistEntry

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_watched.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_data():
    """Create sample members and movies"""
    db = TestingSessionLocal()

    # Create members
    tim = Member(name="Tim", content_filter=ContentRating.ADULT)
    monty = Member(name="Monty", content_filter=ContentRating.ADULT)
    sally = Member(name="Sally", content_filter=ContentRating.TEEN)
    db.add_all([tim, monty, sally])
    db.commit()

    # Create movies
    dune = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
    matrix = Movie(tmdb_id=603, title="The Matrix", year=1999, content_rating=ContentRating.MATURE)
    db.add_all([dune, matrix])
    db.commit()

    # Add to watchlist
    db.add(WatchlistEntry(movie_id=dune.id, added_by_id=tim.id, is_active=True))
    db.add(WatchlistEntry(movie_id=matrix.id, added_by_id=tim.id, is_active=True))
    db.commit()

    db.refresh(tim)
    db.refresh(monty)
    db.refresh(sally)
    db.refresh(dune)
    db.refresh(matrix)

    db.close()

    return {"tim": tim, "monty": monty, "sally": sally, "dune": dune, "matrix": matrix}


class TestMemberWatchedCRUD:
    """Test watched CRUD operations"""

    def test_mark_movie_watched(self, sample_data):
        response = client.post("/api/watched/", json={
            "movie_id": sample_data["dune"].id,
            "member_ids": [sample_data["tim"].id],
            "would_rewatch": False
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["member_id"] == sample_data["tim"].id
        assert data[0]["would_rewatch"] == False

    def test_mark_watched_multiple_members(self, sample_data):
        response = client.post("/api/watched/", json={
            "movie_id": sample_data["dune"].id,
            "member_ids": [sample_data["tim"].id, sample_data["monty"].id],
            "would_rewatch": False
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_member_watched_list(self, sample_data):
        # Mark watched first
        client.post("/api/watched/", json={
            "movie_id": sample_data["dune"].id,
            "member_ids": [sample_data["tim"].id],
            "would_rewatch": True
        })

        response = client.get(f"/api/watched/{sample_data['tim'].id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["movie"]["title"] == "Dune"
        assert data[0]["would_rewatch"] == True

    def test_update_would_rewatch(self, sample_data):
        # Mark watched
        client.post("/api/watched/", json={
            "movie_id": sample_data["dune"].id,
            "member_ids": [sample_data["tim"].id],
            "would_rewatch": False
        })

        # Update to would rewatch
        response = client.patch(
            f"/api/watched/{sample_data['tim'].id}/{sample_data['dune'].id}",
            json={"would_rewatch": True}
        )
        assert response.status_code == 200
        assert response.json()["would_rewatch"] == True


class TestSwipeWithWatched:
    """Test swiping with watched flag"""

    def test_swipe_with_watched_yes(self, sample_data):
        response = client.post("/api/swipes/", json={
            "member_id": sample_data["tim"].id,
            "movie_id": sample_data["dune"].id,
            "direction": "yes",
            "watched": True
        })
        assert response.status_code == 201

        # Check MemberWatched was created with would_rewatch=True
        watched_response = client.get(f"/api/watched/{sample_data['tim'].id}")
        watched = watched_response.json()
        assert len(watched) == 1
        assert watched[0]["would_rewatch"] == True

    def test_swipe_with_watched_no(self, sample_data):
        response = client.post("/api/swipes/", json={
            "member_id": sample_data["tim"].id,
            "movie_id": sample_data["dune"].id,
            "direction": "no",
            "watched": True
        })
        assert response.status_code == 201

        # Check MemberWatched was created with would_rewatch=False
        watched_response = client.get(f"/api/watched/{sample_data['tim'].id}")
        watched = watched_response.json()
        assert len(watched) == 1
        assert watched[0]["would_rewatch"] == False


class TestMovieNightMatching:
    """Test movie night matching with watched status"""

    def test_match_excludes_watched_movies(self, sample_data):
        db = TestingSessionLocal()

        # Tim and Monty both swipe yes on Dune
        db.add(Swipe(member_id=sample_data["tim"].id, movie_id=sample_data["dune"].id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=sample_data["monty"].id, movie_id=sample_data["dune"].id, direction=SwipeDirection.YES))

        # Tim has watched Dune and wouldn't rewatch
        db.add(MemberWatched(member_id=sample_data["tim"].id, movie_id=sample_data["dune"].id, would_rewatch=False))
        db.commit()
        db.close()

        # Movie night with Tim and Monty
        response = client.post("/api/movie-night/matches", json={
            "present_member_ids": [sample_data["tim"].id, sample_data["monty"].id]
        })
        assert response.status_code == 200
        matches = response.json()["matches"]

        # Dune should NOT be a full match because Tim watched it and wouldn't rewatch
        dune_match = next((m for m in matches if m["movie"]["title"] == "Dune"), None)
        if dune_match:
            assert dune_match["is_full_match"] == False

    def test_match_includes_would_rewatch(self, sample_data):
        db = TestingSessionLocal()

        # Tim and Monty both swipe yes on Dune
        db.add(Swipe(member_id=sample_data["tim"].id, movie_id=sample_data["dune"].id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=sample_data["monty"].id, movie_id=sample_data["dune"].id, direction=SwipeDirection.YES))

        # Tim has watched Dune and WOULD rewatch
        db.add(MemberWatched(member_id=sample_data["tim"].id, movie_id=sample_data["dune"].id, would_rewatch=True))
        db.commit()
        db.close()

        # Movie night with Tim and Monty
        response = client.post("/api/movie-night/matches", json={
            "present_member_ids": [sample_data["tim"].id, sample_data["monty"].id]
        })
        assert response.status_code == 200
        matches = response.json()["matches"]

        # Dune SHOULD be a full match because Tim would rewatch
        dune_match = next((m for m in matches if m["movie"]["title"] == "Dune"), None)
        assert dune_match is not None
        assert dune_match["is_full_match"] == True

    def test_unwatched_members_can_match(self, sample_data):
        db = TestingSessionLocal()

        # All three swipe yes on Dune
        db.add(Swipe(member_id=sample_data["tim"].id, movie_id=sample_data["dune"].id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=sample_data["monty"].id, movie_id=sample_data["dune"].id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=sample_data["sally"].id, movie_id=sample_data["dune"].id, direction=SwipeDirection.YES))

        # Tim and Monty watched it
        db.add(MemberWatched(member_id=sample_data["tim"].id, movie_id=sample_data["dune"].id, would_rewatch=False))
        db.add(MemberWatched(member_id=sample_data["monty"].id, movie_id=sample_data["dune"].id, would_rewatch=False))
        db.commit()
        db.close()

        # Movie night with ONLY Sally (who hasn't watched)
        response = client.post("/api/movie-night/matches", json={
            "present_member_ids": [sample_data["sally"].id]
        })
        assert response.status_code == 200
        matches = response.json()["matches"]

        # Dune SHOULD match for Sally alone
        dune_match = next((m for m in matches if m["movie"]["title"] == "Dune"), None)
        assert dune_match is not None
        assert dune_match["is_full_match"] == True
```

**Step 2: Run tests**

```bash
cd backend
source venv/bin/activate
pytest tests/test_member_watched.py -v
```

Expected: All tests pass.

**Step 3: Commit**

```bash
git add backend/tests/test_member_watched.py
git commit -m "test: add comprehensive tests for per-member watched tracking"
```

---

## Task 7: Frontend Types

**Files:**
- Modify: `frontend/src/types/index.ts`

**Step 1: Add MemberWatched type**

Add after `WatchHistory` interface:

```typescript
export interface MemberWatched {
  id: number;
  movie: Movie;
  watched_at: string;
  would_rewatch: boolean;
}
```

**Step 2: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat: add MemberWatched type to frontend"
```

---

## Task 8: Frontend API Client

**Files:**
- Modify: `frontend/src/api/client.ts`

**Step 1: Add import for MemberWatched**

Update the import:

```typescript
import type {
  Member,
  Movie,
  WatchlistEntry,
  WatchHistory,
  SwipeQueue,
  MovieNightResponse,
  RunoffResult,
  TMDBSearchResponse,
  WatchStats,
  SwipeDirection,
  MemberWatched,
} from '../types';
```

**Step 2: Update recordSwipe to accept watched flag**

```typescript
export const recordSwipe = (
  memberId: number,
  movieId: number,
  direction: SwipeDirection,
  watched: boolean = false
) =>
  api.post('/swipes', {
    member_id: memberId,
    movie_id: movieId,
    direction,
    watched,
  }).then(r => r.data);
```

**Step 3: Add watched API functions**

Add at end of file:

```typescript
// Watched
export const getMemberWatched = (memberId: number) =>
  api.get<MemberWatched[]>(`/watched/${memberId}`).then(r => r.data);

export const markMovieWatched = (movieId: number, memberIds: number[], wouldRewatch = false) =>
  api.post('/watched/', {
    movie_id: movieId,
    member_ids: memberIds,
    would_rewatch: wouldRewatch,
  }).then(r => r.data);

export const updateWouldRewatch = (memberId: number, movieId: number, wouldRewatch: boolean) =>
  api.patch(`/watched/${memberId}/${movieId}`, { would_rewatch: wouldRewatch }).then(r => r.data);
```

**Step 4: Commit**

```bash
git add frontend/src/api/client.ts
git commit -m "feat: add watched API functions to frontend client"
```

---

## Task 9: Swipe Screen UI - Watched Toggle

**Files:**
- Modify: `frontend/src/pages/SwipeScreen.tsx`
- Modify: `frontend/src/pages/SwipeScreen.css`

**Step 1: Add watched state to MovieCard component**

In `SwipeScreen.tsx`, update the MovieCard component to include watched toggle.

Add useState import if not present, and add state:

```typescript
function MovieCard({
  movie,
  onSwipe,
  isTop,
}: {
  movie: Movie;
  onSwipe: (direction: SwipeDirection, watched: boolean) => void;
  isTop: boolean;
}) {
  const [watched, setWatched] = useState(false);
```

**Step 2: Update handleDragEnd to pass watched**

```typescript
  const handleDragEnd = useCallback(
    (_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
      const threshold = 100;
      if (info.offset.x > threshold) {
        onSwipe('yes', watched);
      } else if (info.offset.x < -threshold) {
        onSwipe('no', watched);
      }
    },
    [onSwipe, watched]
  );
```

**Step 3: Add watched toggle button to card**

Inside the poster div, after the swipe indicators, add:

```tsx
        <button
          className={`watched-toggle ${watched ? 'active' : ''}`}
          onClick={(e) => {
            e.stopPropagation();
            setWatched(!watched);
          }}
        >
          👁
        </button>
```

**Step 4: Update handleSwipe in SwipeScreen**

```typescript
  const handleSwipe = useCallback(
    (direction: SwipeDirection, watched: boolean = false) => {
      const movie = queue?.movies[currentIndex];
      if (movie) {
        swipeMutation.mutate({ movieId: movie.id, direction, watched });
      }
    },
    [queue, currentIndex, swipeMutation]
  );
```

**Step 5: Update swipeMutation**

```typescript
  const swipeMutation = useMutation({
    mutationFn: ({ movieId, direction, watched }: { movieId: number; direction: SwipeDirection; watched: boolean }) =>
      recordSwipe(memberId!, movieId, direction, watched),
    onSuccess: () => {
      setCurrentIndex((i) => i + 1);
    },
  });
```

**Step 6: Update button handlers**

```tsx
          <motion.button
            className="swipe-btn no"
            onClick={() => handleSwipe('no', false)}
```

and

```tsx
          <motion.button
            className="swipe-btn yes"
            onClick={() => handleSwipe('yes', false)}
```

Note: Button clicks don't pass watched state - only drag gestures do. Users need to toggle watched before swiping.

**Step 7: Add CSS for watched toggle**

In `SwipeScreen.css`, add:

```css
.watched-toggle {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.5);
  background: rgba(0, 0, 0, 0.5);
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  transition: all 0.2s ease;
}

.watched-toggle:hover {
  background: rgba(0, 0, 0, 0.7);
  border-color: rgba(255, 255, 255, 0.8);
}

.watched-toggle.active {
  background: rgba(229, 9, 20, 0.9);
  border-color: #e50914;
  color: #fff;
}
```

**Step 8: Commit**

```bash
git add frontend/src/pages/SwipeScreen.tsx frontend/src/pages/SwipeScreen.css
git commit -m "feat: add watched toggle to swipe screen cards"
```

---

## Task 10: Watchlist - Show Watched Toggle

**Files:**
- Modify: `frontend/src/pages/Watchlist.tsx`

**Step 1: Add state and imports**

Add to imports:

```typescript
import { getMemberWatched, updateWouldRewatch } from '../api/client';
import type { MemberWatched } from '../types';
```

Add state for showing watched:

```typescript
const [showWatched, setShowWatched] = useState(false);
```

**Step 2: Add query for member's watched list**

```typescript
const { data: watchedMovies } = useQuery({
  queryKey: ['memberWatched', memberId],
  queryFn: () => getMemberWatched(memberId!),
  enabled: !!memberId && showWatched,
});
```

**Step 3: Add mutation for updating would_rewatch**

```typescript
const updateRewatchMutation = useMutation({
  mutationFn: ({ movieId, wouldRewatch }: { movieId: number; wouldRewatch: boolean }) =>
    updateWouldRewatch(memberId!, movieId, wouldRewatch),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['memberWatched', memberId] });
  },
});
```

**Step 4: Add toggle in header**

```tsx
<header>
  <h1>{showWatched ? 'Watched' : 'Watchlist'}</h1>
  <label className="show-watched-toggle">
    <span>Show Watched</span>
    <input
      type="checkbox"
      checked={showWatched}
      onChange={(e) => setShowWatched(e.target.checked)}
    />
  </label>
</header>
```

**Step 5: Render watched list when toggled**

```tsx
{showWatched ? (
  <div className="watched-list">
    {watchedMovies?.map((item) => (
      <div key={item.id} className="watched-item">
        <img src={item.movie.poster_url || ''} alt={item.movie.title} />
        <div className="watched-info">
          <h3>{item.movie.title}</h3>
          <p>Watched {new Date(item.watched_at).toLocaleDateString()}</p>
        </div>
        <button
          className={`rewatch-btn ${item.would_rewatch ? 'active' : ''}`}
          onClick={() => updateRewatchMutation.mutate({
            movieId: item.movie.id,
            wouldRewatch: !item.would_rewatch
          })}
        >
          {item.would_rewatch ? '♥' : '♡'}
        </button>
      </div>
    ))}
  </div>
) : (
  // Existing watchlist rendering
  ...
)}
```

**Step 6: Add CSS**

Add to Watchlist.css (or create if needed):

```css
.show-watched-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #888;
}

.show-watched-toggle input {
  width: 18px;
  height: 18px;
}

.watched-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.watched-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: #1a1a2e;
  border-radius: 12px;
}

.watched-item img {
  width: 50px;
  height: 75px;
  object-fit: cover;
  border-radius: 6px;
}

.watched-info {
  flex: 1;
}

.watched-info h3 {
  margin: 0;
  font-size: 1rem;
  color: #fff;
}

.watched-info p {
  margin: 0.25rem 0 0;
  font-size: 0.8rem;
  color: #888;
}

.rewatch-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: #888;
  font-size: 1.5rem;
  cursor: pointer;
}

.rewatch-btn.active {
  background: rgba(229, 9, 20, 0.2);
  color: #e50914;
}
```

**Step 7: Commit**

```bash
git add frontend/src/pages/Watchlist.tsx frontend/src/pages/Watchlist.css
git commit -m "feat: add show watched toggle to watchlist screen"
```

---

## Task 11: Movie Night Completion Flow

**Files:**
- Modify: `frontend/src/pages/MovieNight.tsx`

**Step 1: Add state for completion flow**

```typescript
const [showCompletion, setShowCompletion] = useState(false);
const [selectedWatchers, setSelectedWatchers] = useState<number[]>([]);
```

**Step 2: Add markWatched import**

```typescript
import { getMatches, startRunoff, castVote, getRunoffResult, markMovieWatched } from '../api/client';
```

**Step 3: Add mutation for marking watched**

```typescript
const markWatchedMutation = useMutation({
  mutationFn: ({ movieId, memberIds }: { movieId: number; memberIds: number[] }) =>
    markMovieWatched(movieId, memberIds, false),
  onSuccess: () => {
    // Reset and go back to start
    setShowCompletion(false);
    setResult(null);
    setSelectedWatchers([]);
  },
});
```

**Step 4: Show completion screen after result**

After getting the runoff result, add a "Mark as Watched" button that shows the completion screen:

```tsx
{result && !showCompletion && (
  <div className="result-screen">
    <h2>Tonight's Pick</h2>
    <MovieCard movie={result.winner} />
    <button
      className="mark-watched-btn"
      onClick={() => {
        setSelectedWatchers(presentMembers.map(m => m.id));
        setShowCompletion(true);
      }}
    >
      Mark as Watched
    </button>
    <button className="skip-btn" onClick={() => setResult(null)}>
      Done
    </button>
  </div>
)}

{showCompletion && result && (
  <div className="completion-screen">
    <h2>Who watched it?</h2>
    <MovieCard movie={result.winner} small />
    <div className="watcher-checkboxes">
      {allMembers?.map((member) => (
        <label key={member.id} className="watcher-checkbox">
          <input
            type="checkbox"
            checked={selectedWatchers.includes(member.id)}
            onChange={(e) => {
              if (e.target.checked) {
                setSelectedWatchers([...selectedWatchers, member.id]);
              } else {
                setSelectedWatchers(selectedWatchers.filter(id => id !== member.id));
              }
            }}
          />
          <span>{member.name}</span>
        </label>
      ))}
    </div>
    <button
      className="confirm-watched-btn"
      onClick={() => markWatchedMutation.mutate({
        movieId: result.winner.id,
        memberIds: selectedWatchers
      })}
      disabled={selectedWatchers.length === 0}
    >
      Confirm Watched
    </button>
    <button className="skip-btn" onClick={() => setShowCompletion(false)}>
      Skip
    </button>
  </div>
)}
```

**Step 5: Add CSS for completion screen**

```css
.completion-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  gap: 1.5rem;
}

.watcher-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: 100%;
  max-width: 300px;
}

.watcher-checkbox {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: #1a1a2e;
  border-radius: 8px;
  cursor: pointer;
}

.watcher-checkbox input {
  width: 20px;
  height: 20px;
}

.watcher-checkbox span {
  color: #fff;
  font-size: 1rem;
}

.confirm-watched-btn {
  background: #e50914;
  color: #fff;
  border: none;
  padding: 1rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 12px;
  cursor: pointer;
  width: 100%;
  max-width: 300px;
}

.confirm-watched-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.skip-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 0.9rem;
  cursor: pointer;
  padding: 0.5rem;
}
```

**Step 6: Commit**

```bash
git add frontend/src/pages/MovieNight.tsx frontend/src/pages/MovieNight.css
git commit -m "feat: add movie night completion flow with watched marking"
```

---

## Task 12: Final Integration Test

**Step 1: Restart servers**

```bash
# Backend
pkill -f "uvicorn app.main:app" || true
cd /Users/tim/Claude/Movie_picker/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Frontend
cd /Users/tim/Claude/Movie_picker/frontend
npm run dev -- --host &
```

**Step 2: Manual test checklist**

1. [ ] Open swipe screen - see watched toggle (👁) on movie card
2. [ ] Toggle watched ON, swipe YES - verify MemberWatched created with would_rewatch=true
3. [ ] Toggle watched ON, swipe NO - verify MemberWatched created with would_rewatch=false
4. [ ] Open Watchlist, toggle "Show Watched" - see personal watched list
5. [ ] Tap heart on watched movie to toggle would_rewatch
6. [ ] Start Movie Night - watched movies excluded from matching (unless would_rewatch=true)
7. [ ] Complete Movie Night - see "Mark as Watched" prompt
8. [ ] Select watchers and confirm - verify MemberWatched records created

**Step 3: Run full test suite**

```bash
cd /Users/tim/Claude/Movie_picker/backend
pytest -v
```

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete per-member watched tracking feature

- Add MemberWatched model and database table
- Add watched toggle to swipe screen cards
- Update movie night matching to filter by watched status
- Add watched list view in Watchlist tab
- Add movie night completion flow with watched marking
- Comprehensive test coverage"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Database model | `backend/app/models.py` |
| 2 | Pydantic schemas | `backend/app/schemas.py` |
| 3 | Watched router | `backend/app/routers/watched.py`, `main.py` |
| 4 | Update swipes router | `backend/app/routers/swipes.py` |
| 5 | Update movie night matching | `backend/app/routers/movie_night.py` |
| 6 | Backend tests | `backend/tests/test_member_watched.py` |
| 7 | Frontend types | `frontend/src/types/index.ts` |
| 8 | Frontend API client | `frontend/src/api/client.ts` |
| 9 | Swipe screen UI | `frontend/src/pages/SwipeScreen.tsx`, `.css` |
| 10 | Watchlist toggle | `frontend/src/pages/Watchlist.tsx`, `.css` |
| 11 | Movie night completion | `frontend/src/pages/MovieNight.tsx`, `.css` |
| 12 | Integration testing | Manual + pytest |
