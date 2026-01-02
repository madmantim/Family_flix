import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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
