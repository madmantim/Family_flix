import pytest
from unittest.mock import AsyncMock, patch


def test_search_movies(client):
    """Test movie search endpoint."""
    with patch('app.services.tmdb.TMDBService.search_movies', new_callable=AsyncMock) as mock:
        mock.return_value = {
            "results": [
                {
                    "id": 123,
                    "title": "Test Movie",
                    "overview": "A test movie",
                    "release_date": "2024-01-01",
                    "poster_path": "/test.jpg",
                    "backdrop_path": "/backdrop.jpg",
                    "vote_average": 7.5,
                    "genre_ids": [28, 12]
                }
            ],
            "total_results": 1
        }

        response = client.get("/api/movies/search?query=test")
        assert response.status_code == 200


def test_trending_movies(client):
    """Test trending movies endpoint."""
    with patch('app.services.tmdb.TMDBService.get_trending', new_callable=AsyncMock) as mock:
        mock.return_value = {
            "results": [
                {
                    "id": 456,
                    "title": "Trending Movie",
                    "overview": "A trending movie",
                    "release_date": "2024-06-01",
                    "poster_path": "/trend.jpg",
                    "backdrop_path": None,
                    "vote_average": 8.0,
                    "genre_ids": [18]
                }
            ]
        }

        response = client.get("/api/movies/trending")
        assert response.status_code == 200


def test_search_movies_empty_query(client):
    """Test search with empty query returns error or empty."""
    response = client.get("/api/movies/search?query=")
    # Should either return 400 or empty results
    assert response.status_code in [200, 400, 422]
