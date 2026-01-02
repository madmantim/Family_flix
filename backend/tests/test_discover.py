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
