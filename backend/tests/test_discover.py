import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from app.services.tmdb import TMDBService


@pytest.mark.asyncio
async def test_discover_movies_popular():
    """Test discover_movies with popular sort"""
    mock_response = {
        "results": [{"id": 123, "title": "Test Movie", "release_date": "2025-12-01"}],
        "page": 1,
        "total_pages": 10,
        "total_results": 200
    }

    # Create mock response object
    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_response
    mock_resp.raise_for_status = MagicMock()

    # Create mock client
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp

    with patch("httpx.AsyncClient") as mock_async_client:
        mock_async_client.return_value.__aenter__.return_value = mock_client
        mock_async_client.return_value.__aexit__.return_value = None

        service = TMDBService()
        result = await service.discover_movies(
            sort_by="popularity.desc",
            release_date_gte="2025-10-01",
            release_date_lte="2025-12-31",
            with_release_type="4|5"
        )

        assert result == mock_response
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "discover/movie" in str(call_args)


@pytest.mark.asyncio
async def test_discover_movies_highly_rated():
    """Test discover_movies with vote_average sort and vote_count filter"""
    mock_response = {
        "results": [{"id": 456, "title": "Rated Movie", "release_date": "2025-11-15"}],
        "page": 1,
        "total_pages": 5,
        "total_results": 100
    }

    # Create mock response object
    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_response
    mock_resp.raise_for_status = MagicMock()

    # Create mock client
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp

    with patch("httpx.AsyncClient") as mock_async_client:
        mock_async_client.return_value.__aenter__.return_value = mock_client
        mock_async_client.return_value.__aexit__.return_value = None

        service = TMDBService()
        result = await service.discover_movies(
            sort_by="vote_average.desc",
            release_date_gte="2025-10-01",
            release_date_lte="2025-12-31",
            vote_count_gte=50,
            with_release_type="4|5"
        )

        assert result == mock_response


def test_discover_endpoint_popular(client, mocker):
    """Test GET /movies/discover?tab=popular"""
    mock_results = {
        "results": [
            {"id": 123, "title": "Popular Movie", "release_date": "2025-12-01",
             "overview": "A popular film", "poster_path": "/poster.jpg", "vote_average": 7.5}
        ],
        "page": 1,
        "total_pages": 10,
        "total_results": 200
    }

    # Mock the TMDB service discover_movies method
    mocker.patch(
        "app.services.tmdb.TMDBService.discover_movies",
        new_callable=AsyncMock,
        return_value=mock_results
    )

    response = client.get("/api/movies/discover?tab=popular")

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Popular Movie"


def test_discover_endpoint_highly_rated(client, mocker):
    """Test GET /movies/discover?tab=highly-rated"""
    mock_results = {
        "results": [
            {"id": 456, "title": "Rated Movie", "release_date": "2025-11-15",
             "overview": "A highly rated film", "poster_path": "/rated.jpg", "vote_average": 8.5}
        ],
        "page": 1,
        "total_pages": 5,
        "total_results": 100
    }

    # Mock the TMDB service discover_movies method
    mocker.patch(
        "app.services.tmdb.TMDBService.discover_movies",
        new_callable=AsyncMock,
        return_value=mock_results
    )

    response = client.get("/api/movies/discover?tab=highly-rated")

    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["title"] == "Rated Movie"


def test_discover_endpoint_invalid_tab(client):
    """Test GET /movies/discover with invalid tab returns 422"""
    response = client.get("/api/movies/discover?tab=invalid")
    assert response.status_code == 422  # FastAPI validation error


def test_discover_endpoint_trending_is_home_available(client, mocker):
    """tab=trending should call discover_movies (NOT /trending), restricted to
    Digital+Physical releases. The app is for at-home viewing only; TMDB's
    curated /trending feed surfaces films currently in cinemas only."""
    captured = {}

    async def fake_discover(**kwargs):
        captured.update(kwargs)
        return {"results": [], "page": 1, "total_pages": 0, "total_results": 0}

    trending_mock = mocker.patch(
        "app.services.tmdb.TMDBService.get_trending",
        new_callable=AsyncMock,
    )
    mocker.patch(
        "app.services.tmdb.TMDBService.discover_movies",
        side_effect=fake_discover,
    )

    response = client.get("/api/movies/discover?tab=trending")

    assert response.status_code == 200
    # Must NOT use TMDB's curated trending feed (would include theatrical-only).
    trending_mock.assert_not_called()
    assert captured["sort_by"] == "popularity.desc"
    assert captured["with_release_type"] == "4|5"
    # No date window — older films currently riding a streamer release count.
    assert "release_date_gte" not in captured or captured["release_date_gte"] is None
    assert "release_date_lte" not in captured or captured["release_date_lte"] is None


def test_discover_endpoint_all_time_is_home_available(client, mocker):
    """tab=all-time: top-voted with significant vote count AND home-available."""
    captured = {}

    async def fake_discover(**kwargs):
        captured.update(kwargs)
        return {"results": [], "page": 1, "total_pages": 0, "total_results": 0}

    mocker.patch(
        "app.services.tmdb.TMDBService.discover_movies",
        side_effect=fake_discover,
    )

    response = client.get("/api/movies/discover?tab=all-time")

    assert response.status_code == 200
    assert captured["sort_by"] == "vote_average.desc"
    assert captured["vote_count_gte"] == 1000
    assert captured["with_release_type"] == "4|5"
    # No date window for all-time
    assert "release_date_gte" not in captured or captured["release_date_gte"] is None
    assert "release_date_lte" not in captured or captured["release_date_lte"] is None


def test_discover_endpoint_popular_still_uses_90_day_window(client, mocker):
    """Regression: tab=popular must keep the 90-day release window."""
    captured = {}

    async def fake_discover(**kwargs):
        captured.update(kwargs)
        return {"results": [], "page": 1, "total_pages": 0, "total_results": 0}

    mocker.patch(
        "app.services.tmdb.TMDBService.discover_movies",
        side_effect=fake_discover,
    )

    response = client.get("/api/movies/discover?tab=popular")
    assert response.status_code == 200
    assert captured["sort_by"] == "popularity.desc"
    assert captured["with_release_type"] == "4|5"
    # release_date_gte should be ~90 days ago
    today = datetime.now()
    gte = datetime.strptime(captured["release_date_gte"], "%Y-%m-%d")
    assert 89 <= (today - gte).days <= 91
