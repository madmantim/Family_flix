"""Tests for watchlist router"""
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, get_db
from app.services.tmdb import get_tmdb_service, TMDBService
from app.services.omdb import get_omdb_service, OMDbService
from sqlalchemy.orm import sessionmaker


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


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


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client with mocked external services"""
    app.dependency_overrides[get_tmdb_service] = create_mock_tmdb_service
    app.dependency_overrides[get_omdb_service] = create_mock_omdb_service
    yield TestClient(app)
    # Clean up overrides
    del app.dependency_overrides[get_tmdb_service]
    del app.dependency_overrides[get_omdb_service]


def create_member(test_client, name="Test User"):
    """Helper to create a member"""
    response = test_client.post("/api/members/", json={"name": name})
    assert response.status_code == 201
    return response.json()


def test_add_to_watchlist(client):
    """Test adding a movie to the watchlist"""
    member = create_member(client)

    response = client.post("/api/watchlist/", json={
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


def test_add_duplicate_to_watchlist(client):
    """Test that adding the same movie twice returns an error"""
    member = create_member(client)

    # First add should succeed
    response = client.post("/api/watchlist/", json={
        "tmdb_id": 12345,
        "added_by_id": member["id"]
    })
    assert response.status_code == 201

    # Second add should fail
    response = client.post("/api/watchlist/", json={
        "tmdb_id": 12345,
        "added_by_id": member["id"]
    })
    assert response.status_code == 400
    assert "already in watchlist" in response.json()["detail"].lower()


def test_remove_from_watchlist(client):
    """Test removing a movie from the watchlist (deactivates it)"""
    member = create_member(client)

    # Add movie to watchlist
    add_response = client.post("/api/watchlist/", json={
        "tmdb_id": 12345,
        "added_by_id": member["id"]
    })
    assert add_response.status_code == 201
    entry_id = add_response.json()["id"]

    # Remove it
    remove_response = client.delete(f"/api/watchlist/{entry_id}")
    assert remove_response.status_code == 204

    # Verify it's no longer in active watchlist
    list_response = client.get("/api/watchlist/")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 0


def test_get_watchlist_empty(client):
    """Test getting an empty watchlist"""
    response = client.get("/api/watchlist/")
    assert response.status_code == 200
    assert response.json() == []
