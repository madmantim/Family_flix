"""
Tests for Rotten Tomatoes scores and trailer URL features.

These tests verify:
1. Movie model stores RT scores and trailer URLs correctly
2. API endpoints return RT and trailer data in responses
3. TMDB service extracts trailer URLs from video data
4. OMDb service extracts RT scores (mocked)
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.models import Member, Movie, WatchlistEntry, ContentRating
from app.services.tmdb import TMDBService
from app.services.omdb import OMDbService


class TestMovieModelWithRatingsAndTrailers:
    """Test that Movie model correctly stores RT scores and trailer URLs"""

    def test_movie_stores_rt_critic_score(self, db):
        """Test that RT critic score is stored correctly"""
        movie = Movie(
            tmdb_id=123,
            title="Test Movie",
            content_rating=ContentRating.ALL_AGES,
            rt_critic_score=85
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)

        assert movie.rt_critic_score == 85

    def test_movie_stores_rt_audience_score(self, db):
        """Test that RT audience score is stored correctly"""
        movie = Movie(
            tmdb_id=123,
            title="Test Movie",
            content_rating=ContentRating.ALL_AGES,
            rt_audience_score=92
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)

        assert movie.rt_audience_score == 92

    def test_movie_stores_rt_url(self, db):
        """Test that RT URL is stored correctly"""
        movie = Movie(
            tmdb_id=123,
            title="Test Movie",
            content_rating=ContentRating.ALL_AGES,
            rt_url="https://www.rottentomatoes.com/m/test_movie"
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)

        assert movie.rt_url == "https://www.rottentomatoes.com/m/test_movie"

    def test_movie_stores_trailer_url(self, db):
        """Test that trailer URL is stored correctly"""
        movie = Movie(
            tmdb_id=123,
            title="Test Movie",
            content_rating=ContentRating.ALL_AGES,
            trailer_url="https://www.youtube.com/watch?v=abc123"
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)

        assert movie.trailer_url == "https://www.youtube.com/watch?v=abc123"

    def test_movie_stores_imdb_id(self, db):
        """Test that IMDB ID is stored correctly"""
        movie = Movie(
            tmdb_id=123,
            title="Test Movie",
            content_rating=ContentRating.ALL_AGES,
            imdb_id="tt1234567"
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)

        assert movie.imdb_id == "tt1234567"

    def test_movie_with_all_new_fields(self, db):
        """Test movie with all RT and trailer fields populated"""
        movie = Movie(
            tmdb_id=123,
            title="Complete Movie",
            content_rating=ContentRating.ALL_AGES,
            imdb_id="tt1234567",
            rt_critic_score=88,
            rt_audience_score=91,
            rt_url="https://www.rottentomatoes.com/m/complete_movie",
            trailer_url="https://www.youtube.com/watch?v=xyz789"
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)

        assert movie.imdb_id == "tt1234567"
        assert movie.rt_critic_score == 88
        assert movie.rt_audience_score == 91
        assert movie.rt_url == "https://www.rottentomatoes.com/m/complete_movie"
        assert movie.trailer_url == "https://www.youtube.com/watch?v=xyz789"


class TestSwipeQueueReturnsRatingsAndTrailers:
    """Test that swipe queue API returns RT scores and trailer URLs"""

    def test_swipe_queue_includes_rt_critic_score(self, client, db):
        """Test that swipe queue response includes RT critic score"""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        movie = Movie(
            tmdb_id=123,
            title="Rated Movie",
            content_rating=ContentRating.ALL_AGES,
            rt_critic_score=95
        )
        db.add(movie)
        db.commit()

        db.add(WatchlistEntry(movie_id=movie.id, added_by_id=member.id))
        db.commit()

        resp = client.get(f"/api/swipes/queue/{member.id}")
        assert resp.status_code == 200

        movies = resp.json()["movies"]
        assert len(movies) == 1
        assert movies[0]["rt_critic_score"] == 95

    def test_swipe_queue_includes_rt_audience_score(self, client, db):
        """Test that swipe queue response includes RT audience score"""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        movie = Movie(
            tmdb_id=123,
            title="Rated Movie",
            content_rating=ContentRating.ALL_AGES,
            rt_audience_score=87
        )
        db.add(movie)
        db.commit()

        db.add(WatchlistEntry(movie_id=movie.id, added_by_id=member.id))
        db.commit()

        resp = client.get(f"/api/swipes/queue/{member.id}")
        movies = resp.json()["movies"]
        assert movies[0]["rt_audience_score"] == 87

    def test_swipe_queue_includes_rt_url(self, client, db):
        """Test that swipe queue response includes RT URL"""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        movie = Movie(
            tmdb_id=123,
            title="Rated Movie",
            content_rating=ContentRating.ALL_AGES,
            rt_url="https://www.rottentomatoes.com/m/rated_movie"
        )
        db.add(movie)
        db.commit()

        db.add(WatchlistEntry(movie_id=movie.id, added_by_id=member.id))
        db.commit()

        resp = client.get(f"/api/swipes/queue/{member.id}")
        movies = resp.json()["movies"]
        assert movies[0]["rt_url"] == "https://www.rottentomatoes.com/m/rated_movie"

    def test_swipe_queue_includes_trailer_url(self, client, db):
        """Test that swipe queue response includes trailer URL"""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        movie = Movie(
            tmdb_id=123,
            title="Movie With Trailer",
            content_rating=ContentRating.ALL_AGES,
            trailer_url="https://www.youtube.com/watch?v=trailer123"
        )
        db.add(movie)
        db.commit()

        db.add(WatchlistEntry(movie_id=movie.id, added_by_id=member.id))
        db.commit()

        resp = client.get(f"/api/swipes/queue/{member.id}")
        movies = resp.json()["movies"]
        assert movies[0]["trailer_url"] == "https://www.youtube.com/watch?v=trailer123"

    def test_swipe_queue_includes_imdb_id(self, client, db):
        """Test that swipe queue response includes IMDB ID"""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        movie = Movie(
            tmdb_id=123,
            title="Movie With IMDB",
            content_rating=ContentRating.ALL_AGES,
            imdb_id="tt9876543"
        )
        db.add(movie)
        db.commit()

        db.add(WatchlistEntry(movie_id=movie.id, added_by_id=member.id))
        db.commit()

        resp = client.get(f"/api/swipes/queue/{member.id}")
        movies = resp.json()["movies"]
        assert movies[0]["imdb_id"] == "tt9876543"

    def test_swipe_queue_handles_null_ratings(self, client, db):
        """Test that swipe queue works when ratings are null"""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        movie = Movie(
            tmdb_id=123,
            title="Unrated Movie",
            content_rating=ContentRating.ALL_AGES
            # No RT scores or trailer
        )
        db.add(movie)
        db.commit()

        db.add(WatchlistEntry(movie_id=movie.id, added_by_id=member.id))
        db.commit()

        resp = client.get(f"/api/swipes/queue/{member.id}")
        assert resp.status_code == 200
        movies = resp.json()["movies"]
        assert movies[0]["rt_critic_score"] is None
        assert movies[0]["rt_audience_score"] is None
        assert movies[0]["rt_url"] is None
        assert movies[0]["trailer_url"] is None


class TestWatchlistReturnsRatingsAndTrailers:
    """Test that watchlist API returns RT scores and trailer URLs"""

    def test_watchlist_includes_all_new_fields(self, client, db):
        """Test that watchlist response includes all new fields"""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        movie = Movie(
            tmdb_id=123,
            title="Full Movie",
            content_rating=ContentRating.ALL_AGES,
            imdb_id="tt1111111",
            rt_critic_score=90,
            rt_audience_score=85,
            rt_url="https://www.rottentomatoes.com/m/full_movie",
            trailer_url="https://www.youtube.com/watch?v=full123"
        )
        db.add(movie)
        db.commit()

        db.add(WatchlistEntry(movie_id=movie.id, added_by_id=member.id))
        db.commit()

        resp = client.get("/api/watchlist/")
        assert resp.status_code == 200

        entries = resp.json()
        assert len(entries) == 1
        movie_data = entries[0]["movie"]
        assert movie_data["imdb_id"] == "tt1111111"
        assert movie_data["rt_critic_score"] == 90
        assert movie_data["rt_audience_score"] == 85
        assert movie_data["rt_url"] == "https://www.rottentomatoes.com/m/full_movie"
        assert movie_data["trailer_url"] == "https://www.youtube.com/watch?v=full123"


class TestTMDBServiceTrailerExtraction:
    """Test TMDB service trailer URL extraction logic"""

    def test_extracts_official_trailer(self):
        """Test that official trailers are preferred"""
        tmdb_data = {
            "videos": {
                "results": [
                    {"key": "unofficial1", "site": "YouTube", "type": "Trailer", "official": False},
                    {"key": "official1", "site": "YouTube", "type": "Trailer", "official": True},
                ]
            }
        }
        url = TMDBService.get_trailer_url(tmdb_data)
        assert url == "https://www.youtube.com/watch?v=official1"

    def test_extracts_unofficial_trailer_if_no_official(self):
        """Test that unofficial trailers are used if no official ones"""
        tmdb_data = {
            "videos": {
                "results": [
                    {"key": "unofficial1", "site": "YouTube", "type": "Trailer", "official": False},
                ]
            }
        }
        url = TMDBService.get_trailer_url(tmdb_data)
        assert url == "https://www.youtube.com/watch?v=unofficial1"

    def test_prefers_trailer_over_teaser(self):
        """Test that trailers are preferred over teasers"""
        tmdb_data = {
            "videos": {
                "results": [
                    {"key": "teaser1", "site": "YouTube", "type": "Teaser", "official": True},
                    {"key": "trailer1", "site": "YouTube", "type": "Trailer", "official": True},
                ]
            }
        }
        url = TMDBService.get_trailer_url(tmdb_data)
        assert url == "https://www.youtube.com/watch?v=trailer1"

    def test_falls_back_to_teaser(self):
        """Test that teasers are used if no trailers available"""
        tmdb_data = {
            "videos": {
                "results": [
                    {"key": "teaser1", "site": "YouTube", "type": "Teaser", "official": True},
                ]
            }
        }
        url = TMDBService.get_trailer_url(tmdb_data)
        assert url == "https://www.youtube.com/watch?v=teaser1"

    def test_ignores_non_youtube_videos(self):
        """Test that non-YouTube videos are ignored"""
        tmdb_data = {
            "videos": {
                "results": [
                    {"key": "vimeo1", "site": "Vimeo", "type": "Trailer", "official": True},
                    {"key": "youtube1", "site": "YouTube", "type": "Trailer", "official": True},
                ]
            }
        }
        url = TMDBService.get_trailer_url(tmdb_data)
        assert url == "https://www.youtube.com/watch?v=youtube1"

    def test_returns_none_for_no_videos(self):
        """Test that None is returned when no videos available"""
        tmdb_data = {"videos": {"results": []}}
        url = TMDBService.get_trailer_url(tmdb_data)
        assert url is None

    def test_returns_none_for_missing_videos_key(self):
        """Test that None is returned when videos key is missing"""
        tmdb_data = {}
        url = TMDBService.get_trailer_url(tmdb_data)
        assert url is None

    def test_ignores_clips_and_featurettes(self):
        """Test that clips and featurettes are not used"""
        tmdb_data = {
            "videos": {
                "results": [
                    {"key": "clip1", "site": "YouTube", "type": "Clip", "official": True},
                    {"key": "feat1", "site": "YouTube", "type": "Featurette", "official": True},
                ]
            }
        }
        url = TMDBService.get_trailer_url(tmdb_data)
        assert url is None


class TestOMDbServiceRatingExtraction:
    """Test OMDb service rating extraction logic"""

    @pytest.mark.asyncio
    async def test_extracts_rt_critic_score(self):
        """Test that RT critic score is extracted from OMDb response"""
        omdb = OMDbService()
        omdb.api_key = "test_key"

        mock_response_data = {
            "Response": "True",
            "Title": "Test Movie",
            "Year": "2024",
            "Ratings": [
                {"Source": "Internet Movie Database", "Value": "8.5/10"},
                {"Source": "Rotten Tomatoes", "Value": "92%"},
                {"Source": "Metacritic", "Value": "85/100"}
            ]
        }

        with patch('app.services.omdb.httpx.AsyncClient') as mock_client:
            # Create mock response with synchronous json() method
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data

            # Create async mock for get() that returns the response
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await omdb.get_ratings_by_imdb_id("tt1234567")

            assert result is not None
            assert result["rt_critic_score"] == 92

    @pytest.mark.asyncio
    async def test_handles_missing_rt_rating(self):
        """Test that missing RT rating returns None"""
        omdb = OMDbService()
        omdb.api_key = "test_key"

        mock_response_data = {
            "Response": "True",
            "Title": "Test Movie",
            "Year": "2024",
            "Ratings": [
                {"Source": "Internet Movie Database", "Value": "8.5/10"},
            ]
        }

        with patch('app.services.omdb.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data

            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await omdb.get_ratings_by_imdb_id("tt1234567")

            assert result is not None
            assert result["rt_critic_score"] is None

    @pytest.mark.asyncio
    async def test_constructs_rt_url_from_title(self):
        """Test that RT URL is constructed from movie title"""
        omdb = OMDbService()
        omdb.api_key = "test_key"

        mock_response_data = {
            "Response": "True",
            "Title": "The Dark Knight",
            "Year": "2008",
            "Ratings": []
        }

        with patch('app.services.omdb.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data

            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await omdb.get_ratings_by_imdb_id("tt1234567")

            assert result is not None
            assert "rottentomatoes.com/m/" in result["rt_url"]
            assert "dark" in result["rt_url"].lower()

    @pytest.mark.asyncio
    async def test_returns_none_for_api_error(self):
        """Test that None is returned on API error"""
        omdb = OMDbService()
        omdb.api_key = "test_key"

        with patch('app.services.omdb.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500

            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await omdb.get_ratings_by_imdb_id("tt1234567")

            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_movie_not_found(self):
        """Test that None is returned when movie not found"""
        omdb = OMDbService()
        omdb.api_key = "test_key"

        mock_response_data = {"Response": "False", "Error": "Movie not found!"}

        with patch('app.services.omdb.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data

            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await omdb.get_ratings_by_imdb_id("tt9999999")

            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_no_api_key(self):
        """Test that None is returned when no API key configured"""
        omdb = OMDbService()
        omdb.api_key = ""

        result = await omdb.get_ratings_by_imdb_id("tt1234567")

        assert result is None


class TestMovieNightReturnsRatingsAndTrailers:
    """Test that movie night matches include RT scores and trailer URLs"""

    def test_movie_night_matches_include_new_fields(self, client, db):
        """Test that movie night matches include all new fields"""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        movie = Movie(
            tmdb_id=123,
            title="Match Movie",
            content_rating=ContentRating.ALL_AGES,
            imdb_id="tt2222222",
            rt_critic_score=88,
            rt_audience_score=92,
            rt_url="https://www.rottentomatoes.com/m/match_movie",
            trailer_url="https://www.youtube.com/watch?v=match123"
        )
        db.add(movie)
        db.commit()

        db.add(WatchlistEntry(movie_id=movie.id, added_by_id=member.id))
        db.commit()

        # Add a YES vote
        client.post("/api/swipes/", json={
            "member_id": member.id,
            "movie_id": movie.id,
            "direction": "yes"
        })

        # Get matches
        resp = client.post("/api/movie-night/matches", json={
            "present_member_ids": [member.id]
        })
        assert resp.status_code == 200

        matches = resp.json()["matches"]
        assert len(matches) >= 1

        movie_data = matches[0]["movie"]
        assert movie_data["imdb_id"] == "tt2222222"
        assert movie_data["rt_critic_score"] == 88
        assert movie_data["rt_audience_score"] == 92
        assert movie_data["rt_url"] == "https://www.rottentomatoes.com/m/match_movie"
        assert movie_data["trailer_url"] == "https://www.youtube.com/watch?v=match123"


class TestHistoryReturnsRatingsAndTrailers:
    """Test that watch history includes RT scores and trailer URLs"""

    def test_history_includes_new_fields(self, client, db):
        """Test that watch history entries include all new fields"""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        movie = Movie(
            tmdb_id=123,
            title="Watched Movie",
            content_rating=ContentRating.ALL_AGES,
            imdb_id="tt3333333",
            rt_critic_score=75,
            rt_audience_score=80,
            rt_url="https://www.rottentomatoes.com/m/watched_movie",
            trailer_url="https://www.youtube.com/watch?v=watched123"
        )
        db.add(movie)
        db.commit()

        # Mark as watched using new /watched/ endpoint
        resp = client.post("/api/watched/", json={
            "movie_id": movie.id,
            "member_ids": [member.id],
            "would_rewatch": False
        })
        assert resp.status_code == 200

        # Get history via new endpoint
        history_resp = client.get("/api/watched/history/all")
        assert history_resp.status_code == 200
        assert len(history_resp.json()) == 1

        movie_data = history_resp.json()[0]["movie"]
        assert movie_data["imdb_id"] == "tt3333333"
        assert movie_data["rt_critic_score"] == 75
        assert movie_data["rt_audience_score"] == 80
        assert movie_data["rt_url"] == "https://www.rottentomatoes.com/m/watched_movie"
        assert movie_data["trailer_url"] == "https://www.youtube.com/watch?v=watched123"
