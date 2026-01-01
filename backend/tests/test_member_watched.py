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
