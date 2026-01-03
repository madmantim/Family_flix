"""Tests for per-member watched tracking feature"""
import pytest
from app.models import Member, Movie, Swipe, MemberWatched, SwipeDirection, ContentRating, WatchlistEntry


class TestMemberWatchedCRUD:
    """Test watched CRUD operations"""

    def test_mark_movie_watched(self, client, db):
        # Create member and movie
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        db.commit()

        movie = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(movie)
        db.commit()

        response = client.post("/api/watched/", json={
            "movie_id": movie.id,
            "member_ids": [member.id]
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["member_id"] == member.id

    def test_mark_watched_multiple_members(self, client, db):
        # Create members and movie
        tim = Member(name="Tim", content_filter=ContentRating.ADULT)
        monty = Member(name="Monty", content_filter=ContentRating.ADULT)
        db.add_all([tim, monty])
        db.commit()

        movie = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(movie)
        db.commit()

        response = client.post("/api/watched/", json={
            "movie_id": movie.id,
            "member_ids": [tim.id, monty.id]
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_member_watched_list(self, client, db):
        # Create member and movie
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        db.commit()

        movie = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(movie)
        db.commit()

        # Mark watched first
        client.post("/api/watched/", json={
            "movie_id": movie.id,
            "member_ids": [member.id]
        })

        response = client.get(f"/api/watched/{member.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["movie"]["title"] == "Dune"

    def test_mark_watched_flips_swipe_to_no(self, client, db):
        """When marking a movie as watched, the swipe should flip to NO"""
        # Create member and movie
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        db.commit()

        movie = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(movie)
        db.commit()

        # Add YES swipe
        db.add(Swipe(member_id=member.id, movie_id=movie.id, direction=SwipeDirection.YES))
        db.commit()

        # Mark as watched
        response = client.post("/api/watched/", json={
            "movie_id": movie.id,
            "member_ids": [member.id]
        })
        assert response.status_code == 200

        # Check swipe was flipped to NO
        swipe = db.query(Swipe).filter(
            Swipe.member_id == member.id,
            Swipe.movie_id == movie.id
        ).first()
        assert swipe.direction == SwipeDirection.NO


class TestSwipeWithWatched:
    """Test swiping with watched flag"""

    def test_swipe_with_watched_creates_record(self, client, db):
        # Create member and movie
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        db.commit()

        movie = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(movie)
        db.commit()

        # Add to watchlist
        db.add(WatchlistEntry(movie_id=movie.id, added_by_id=member.id, is_active=True))
        db.commit()

        response = client.post("/api/swipes/", json={
            "member_id": member.id,
            "movie_id": movie.id,
            "direction": "yes",
            "watched": True
        })
        assert response.status_code == 201

        # Check MemberWatched was created
        watched_response = client.get(f"/api/watched/{member.id}")
        watched = watched_response.json()
        assert len(watched) == 1


class TestMovieNightMatching:
    """Test movie night matching with watched status"""

    def test_match_ranking_by_yes_votes(self, client, db):
        """Movies should be ranked by Y-count (yes votes)"""
        # Create members
        tim = Member(name="Tim", content_filter=ContentRating.ADULT)
        monty = Member(name="Monty", content_filter=ContentRating.ADULT)
        sally = Member(name="Sally", content_filter=ContentRating.ADULT)
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

        # Dune: all 3 vote yes
        db.add(Swipe(member_id=tim.id, movie_id=dune.id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=monty.id, movie_id=dune.id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=sally.id, movie_id=dune.id, direction=SwipeDirection.YES))

        # Matrix: only 2 vote yes
        db.add(Swipe(member_id=tim.id, movie_id=matrix.id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=monty.id, movie_id=matrix.id, direction=SwipeDirection.YES))
        db.commit()

        # Movie night with all 3
        response = client.post("/api/movie-night/matches", json={
            "present_member_ids": [tim.id, monty.id, sally.id]
        })
        assert response.status_code == 200
        matches = response.json()["matches"]

        # Dune should be first (3 votes), Matrix second (2 votes)
        assert len(matches) >= 2
        assert matches[0]["movie"]["title"] == "Dune"
        assert matches[0]["yes_votes"] == 3
        assert matches[1]["movie"]["title"] == "The Matrix"
        assert matches[1]["yes_votes"] == 2

    def test_match_includes_movies_with_watched_no_voters(self, client, db):
        """Movies with N(W) voters (watched + no vote) should still show but rank lower"""
        # Create members
        tim = Member(name="Tim", content_filter=ContentRating.ADULT)
        monty = Member(name="Monty", content_filter=ContentRating.ADULT)
        db.add_all([tim, monty])
        db.commit()

        # Create movie
        dune = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(dune)
        db.commit()

        # Add to watchlist
        db.add(WatchlistEntry(movie_id=dune.id, added_by_id=tim.id, is_active=True))
        db.commit()

        # Monty votes yes, Tim has watched but has NO vote
        db.add(Swipe(member_id=monty.id, movie_id=dune.id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=tim.id, movie_id=dune.id, direction=SwipeDirection.NO))
        db.add(MemberWatched(member_id=tim.id, movie_id=dune.id))
        db.commit()

        # Movie night with Tim and Monty
        response = client.post("/api/movie-night/matches", json={
            "present_member_ids": [tim.id, monty.id]
        })
        assert response.status_code == 200
        matches = response.json()["matches"]

        # Dune should still appear (not blocked), with 1 yes vote
        dune_match = next((m for m in matches if m["movie"]["title"] == "Dune"), None)
        assert dune_match is not None
        assert dune_match["yes_votes"] == 1
        assert dune_match["is_full_match"] == False

    def test_full_match_when_all_vote_yes(self, client, db):
        """A movie is a full match when all present members voted YES"""
        # Create members
        tim = Member(name="Tim", content_filter=ContentRating.ADULT)
        monty = Member(name="Monty", content_filter=ContentRating.ADULT)
        db.add_all([tim, monty])
        db.commit()

        # Create movie
        dune = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(dune)
        db.commit()

        # Add to watchlist
        db.add(WatchlistEntry(movie_id=dune.id, added_by_id=tim.id, is_active=True))
        db.commit()

        # Both vote yes
        db.add(Swipe(member_id=tim.id, movie_id=dune.id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=monty.id, movie_id=dune.id, direction=SwipeDirection.YES))
        db.commit()

        # Movie night with Tim and Monty
        response = client.post("/api/movie-night/matches", json={
            "present_member_ids": [tim.id, monty.id]
        })
        assert response.status_code == 200
        matches = response.json()["matches"]

        # Dune should be a full match
        dune_match = next((m for m in matches if m["movie"]["title"] == "Dune"), None)
        assert dune_match is not None
        assert dune_match["is_full_match"] == True
        assert dune_match["yes_votes"] == 2


class TestWatchedToggleAndDelete:
    """Test PUT toggle and DELETE endpoints for watched status"""

    def test_toggle_watched_marks_as_watched(self, client, db):
        """Test PUT endpoint marks movie as watched."""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        db.commit()

        movie = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(movie)
        db.commit()

        # Toggle on (mark watched)
        response = client.put(f"/api/watched/{member.id}/{movie.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["member_id"] == member.id
        assert data["movie_id"] == movie.id

    def test_toggle_watched_returns_existing(self, client, db):
        """Test PUT returns existing record if already watched."""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        db.commit()

        movie = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(movie)
        db.commit()

        # Mark as watched first
        watched = MemberWatched(member_id=member.id, movie_id=movie.id)
        db.add(watched)
        db.commit()

        # Toggle again - should return existing
        response = client.put(f"/api/watched/{member.id}/{movie.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == watched.id

    def test_delete_watched_record(self, client, db):
        """Test DELETE endpoint removes watched record."""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        db.commit()

        movie = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(movie)
        db.commit()

        # Mark as watched first
        watched = MemberWatched(member_id=member.id, movie_id=movie.id)
        db.add(watched)
        db.commit()

        # Delete
        response = client.delete(f"/api/watched/{member.id}/{movie.id}")
        assert response.status_code == 204

        # Verify gone
        get_response = client.get(f"/api/watched/{member.id}")
        data = get_response.json()
        movie_ids = [w["movie"]["id"] for w in data]
        assert movie.id not in movie_ids

    def test_delete_nonexistent_watched(self, client, db):
        """Test deleting non-existent watched record returns 404."""
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        db.commit()

        movie = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(movie)
        db.commit()

        # Try to delete without having marked watched
        response = client.delete(f"/api/watched/{member.id}/{movie.id}")
        assert response.status_code == 404
