"""Tests for watchlist router"""
import pytest
from unittest.mock import AsyncMock
from app.models import Member, Movie, ContentRating, Swipe, SwipeDirection, MemberWatched, WatchlistEntry
from app.services.tmdb import get_tmdb_service, TMDBService
from app.services.omdb import get_omdb_service, OMDbService
from app.main import app


def create_mock_tmdb_service():
    """Create a mock TMDB service"""
    mock = AsyncMock(spec=TMDBService)
    mock.get_movie = AsyncMock(return_value={
        "id": 12345,
        "title": "Test Movie",
        "overview": "A test movie",
        "release_date": "2024-01-15",
        "poster_path": "/test.jpg",
        "backdrop_path": "/backdrop.jpg",
        "vote_average": 7.5,
        "runtime": 120,
        "genres": [{"name": "Action"}, {"name": "Drama"}],
        "imdb_id": "tt1234567",
        "release_dates": {"results": []},
        "videos": {"results": []}
    })
    return mock


def create_mock_omdb_service():
    """Create a mock OMDb service"""
    mock = AsyncMock(spec=OMDbService)
    mock.get_ratings_by_imdb_id = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def watchlist_client(client):
    """Create test client with mocked external services for watchlist tests"""
    app.dependency_overrides[get_tmdb_service] = create_mock_tmdb_service
    app.dependency_overrides[get_omdb_service] = create_mock_omdb_service
    yield client
    # Clean up overrides (keep get_db override from conftest)
    if get_tmdb_service in app.dependency_overrides:
        del app.dependency_overrides[get_tmdb_service]
    if get_omdb_service in app.dependency_overrides:
        del app.dependency_overrides[get_omdb_service]


def create_member(test_client, name="Test User"):
    """Helper to create a member"""
    response = test_client.post("/api/members/", json={"name": name})
    assert response.status_code == 201
    return response.json()


def test_add_to_watchlist(watchlist_client):
    """Test adding a movie to the watchlist"""
    member = create_member(watchlist_client)

    response = watchlist_client.post("/api/watchlist/", json={
        "tmdb_id": 12345,
        "added_by_id": member["id"],
        "source": "manual"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["movie"]["title"] == "Test Movie"
    assert data["movie"]["tmdb_id"] == 12345
    assert data["added_by"]["id"] == member["id"]
    assert data["source"] == "manual"
    assert data["is_active"] is True


def test_add_duplicate_to_watchlist(watchlist_client):
    """Test that adding the same movie twice returns an error"""
    member = create_member(watchlist_client)

    # First add should succeed
    response = watchlist_client.post("/api/watchlist/", json={
        "tmdb_id": 12345,
        "added_by_id": member["id"]
    })
    assert response.status_code == 201

    # Second add should fail
    response = watchlist_client.post("/api/watchlist/", json={
        "tmdb_id": 12345,
        "added_by_id": member["id"]
    })
    assert response.status_code == 400
    assert "already in watchlist" in response.json()["detail"].lower()


def test_remove_from_watchlist(watchlist_client):
    """Test removing a movie from the watchlist (deactivates it)"""
    member = create_member(watchlist_client)

    # Add movie to watchlist
    add_response = watchlist_client.post("/api/watchlist/", json={
        "tmdb_id": 12345,
        "added_by_id": member["id"]
    })
    assert add_response.status_code == 201
    entry_id = add_response.json()["id"]

    # Remove it
    remove_response = watchlist_client.delete(f"/api/watchlist/{entry_id}")
    assert remove_response.status_code == 204

    # Verify it's no longer in active watchlist
    list_response = watchlist_client.get("/api/watchlist/")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 0


def test_get_watchlist_empty(watchlist_client):
    """Test getting an empty watchlist"""
    response = watchlist_client.get("/api/watchlist/")
    assert response.status_code == 200
    assert response.json() == []


def _setup_bulk_fixture(client, db):
    """Seed two members, three movies, and existing YES swipes from m1 on all three."""
    m1 = Member(name="Tim", content_filter=ContentRating.ADULT)
    m2 = Member(name="Beck", content_filter=ContentRating.ADULT)
    db.add_all([m1, m2])
    db.commit()

    movies = [
        Movie(tmdb_id=100 + i, title=f"Movie {i}", content_rating=ContentRating.ALL_AGES)
        for i in range(3)
    ]
    db.add_all(movies)
    db.commit()

    # m1 voted YES on all three; m2 also voted YES on the first
    for movie in movies:
        db.add(Swipe(member_id=m1.id, movie_id=movie.id, direction=SwipeDirection.YES))
        db.add(WatchlistEntry(movie_id=movie.id, added_by_id=m1.id))
    db.add(Swipe(member_id=m2.id, movie_id=movies[0].id, direction=SwipeDirection.YES))
    db.commit()
    return m1, m2, movies


def test_bulk_update_mark_watched_and_remove(client, db):
    """Action 1: mark watched + flip swipes to NO for the requesting member only."""
    m1, m2, movies = _setup_bulk_fixture(client, db)

    resp = client.post("/api/watchlist/bulk-update", json={
        "member_id": m1.id,
        "movie_ids": [movies[0].id, movies[1].id],
        "mark_watched": True,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["updated_count"] == 2
    assert body["watched_recorded"] == 2

    # m1's swipes on those movies are now NO
    m1_swipes = {s.movie_id: s.direction for s in db.query(Swipe).filter(Swipe.member_id == m1.id).all()}
    assert m1_swipes[movies[0].id] == SwipeDirection.NO
    assert m1_swipes[movies[1].id] == SwipeDirection.NO
    assert m1_swipes[movies[2].id] == SwipeDirection.YES  # untouched

    # m1 has watched records for both
    watched = {w.movie_id for w in db.query(MemberWatched).filter(MemberWatched.member_id == m1.id).all()}
    assert watched == {movies[0].id, movies[1].id}

    # m2's YES on movie 0 is unaffected — personal-only
    m2_swipe = db.query(Swipe).filter(Swipe.member_id == m2.id, Swipe.movie_id == movies[0].id).first()
    assert m2_swipe.direction == SwipeDirection.YES


def test_bulk_update_just_remove(client, db):
    """Action 2: flip swipes to NO but no watched record."""
    m1, _, movies = _setup_bulk_fixture(client, db)

    resp = client.post("/api/watchlist/bulk-update", json={
        "member_id": m1.id,
        "movie_ids": [movies[0].id, movies[2].id],
        "mark_watched": False,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["updated_count"] == 2
    assert body["watched_recorded"] == 0

    swipes = {s.movie_id: s.direction for s in db.query(Swipe).filter(Swipe.member_id == m1.id).all()}
    assert swipes[movies[0].id] == SwipeDirection.NO
    assert swipes[movies[2].id] == SwipeDirection.NO
    assert swipes[movies[1].id] == SwipeDirection.YES  # untouched

    # No watched records created
    watched = db.query(MemberWatched).filter(MemberWatched.member_id == m1.id).count()
    assert watched == 0


def test_bulk_update_idempotent(client, db):
    """Running the same bulk action twice doesn't duplicate MemberWatched rows."""
    m1, _, movies = _setup_bulk_fixture(client, db)

    for _ in range(2):
        resp = client.post("/api/watchlist/bulk-update", json={
            "member_id": m1.id,
            "movie_ids": [movies[0].id],
            "mark_watched": True,
        })
        assert resp.status_code == 200

    watched = db.query(MemberWatched).filter(
        MemberWatched.member_id == m1.id,
        MemberWatched.movie_id == movies[0].id,
    ).count()
    assert watched == 1


def test_bulk_update_does_not_touch_shared_pool(client, db):
    """The shared WatchlistEntry rows remain active after either action."""
    m1, _, movies = _setup_bulk_fixture(client, db)

    client.post("/api/watchlist/bulk-update", json={
        "member_id": m1.id,
        "movie_ids": [movies[0].id, movies[1].id, movies[2].id],
        "mark_watched": True,
    })

    active_count = db.query(WatchlistEntry).filter(WatchlistEntry.is_active == True).count()
    assert active_count == 3  # all three still in the pool


def test_bulk_update_unknown_movie_returns_404(client, db):
    m1, _, movies = _setup_bulk_fixture(client, db)
    resp = client.post("/api/watchlist/bulk-update", json={
        "member_id": m1.id,
        "movie_ids": [movies[0].id, 99999],
        "mark_watched": False,
    })
    assert resp.status_code == 404


def test_bulk_update_unknown_member_returns_404(client, db):
    _, _, movies = _setup_bulk_fixture(client, db)
    resp = client.post("/api/watchlist/bulk-update", json={
        "member_id": 99999,
        "movie_ids": [movies[0].id],
        "mark_watched": False,
    })
    assert resp.status_code == 404


def test_bulk_update_dedupes_movie_ids(client, db):
    """Duplicate movie_ids in the payload are silently deduped."""
    m1, _, movies = _setup_bulk_fixture(client, db)
    resp = client.post("/api/watchlist/bulk-update", json={
        "member_id": m1.id,
        "movie_ids": [movies[0].id, movies[0].id, movies[1].id],
        "mark_watched": True,
    })
    assert resp.status_code == 200
    assert resp.json()["updated_count"] == 2
    assert resp.json()["watched_recorded"] == 2


def test_bulk_update_recovers_from_concurrent_race(client, db, mocker):
    """Simulate a concurrent bulk request inserting a MemberWatched row between
    our query and our commit: the first commit raises IntegrityError, and we
    retry. The endpoint must return 200 and reflect the converged state."""
    from app.routers import watchlist as watchlist_router
    m1, _, movies = _setup_bulk_fixture(client, db)

    # Have the "other" request beat us to MemberWatched on movie 0.
    db.add(MemberWatched(member_id=m1.id, movie_id=movies[0].id))
    db.commit()

    # Force the first call to _apply_bulk_updates to think the row isn't
    # there (simulating a stale read), which will cause the commit to fail
    # with IntegrityError. The retry should re-read fresh state and succeed.
    original = watchlist_router._apply_bulk_updates
    calls = {"n": 0}

    def fake_apply(db_session, *, member_id, movie_ids, mark_watched):
        calls["n"] += 1
        if calls["n"] == 1:
            # On the first try, pretend the existing watched row doesn't exist
            # by directly adding a duplicate to provoke IntegrityError.
            db_session.add(MemberWatched(member_id=member_id, movie_id=movies[0].id))
            # Also do the swipe work so the rest of the path is exercised.
            db_session.query(Swipe).filter(
                Swipe.member_id == member_id,
                Swipe.movie_id == movies[0].id,
            ).update({Swipe.direction: SwipeDirection.NO})
            return 1
        return original(db_session, member_id=member_id, movie_ids=movie_ids, mark_watched=mark_watched)

    mocker.patch.object(watchlist_router, "_apply_bulk_updates", side_effect=fake_apply)

    resp = client.post("/api/watchlist/bulk-update", json={
        "member_id": m1.id,
        "movie_ids": [movies[0].id, movies[1].id],
        "mark_watched": True,
    })
    assert resp.status_code == 200
    assert calls["n"] == 2  # retried once
    assert resp.json()["updated_count"] == 2
