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
            "member_ids": [member.id],
            "would_rewatch": False
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["member_id"] == member.id
        assert data[0]["would_rewatch"] == False

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
            "member_ids": [tim.id, monty.id],
            "would_rewatch": False
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
            "member_ids": [member.id],
            "would_rewatch": True
        })

        response = client.get(f"/api/watched/{member.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["movie"]["title"] == "Dune"
        assert data[0]["would_rewatch"] == True

    def test_update_would_rewatch(self, client, db):
        # Create member and movie
        member = Member(name="Tim", content_filter=ContentRating.ADULT)
        db.add(member)
        db.commit()

        movie = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(movie)
        db.commit()

        # Mark watched
        client.post("/api/watched/", json={
            "movie_id": movie.id,
            "member_ids": [member.id],
            "would_rewatch": False
        })

        # Update to would rewatch
        response = client.patch(
            f"/api/watched/{member.id}/{movie.id}",
            json={"would_rewatch": True}
        )
        assert response.status_code == 200
        assert response.json()["would_rewatch"] == True


class TestSwipeWithWatched:
    """Test swiping with watched flag"""

    def test_swipe_with_watched_yes(self, client, db):
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

        # Check MemberWatched was created with would_rewatch=True
        watched_response = client.get(f"/api/watched/{member.id}")
        watched = watched_response.json()
        assert len(watched) == 1
        assert watched[0]["would_rewatch"] == True

    def test_swipe_with_watched_no(self, client, db):
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
            "direction": "no",
            "watched": True
        })
        assert response.status_code == 201

        # Check MemberWatched was created with would_rewatch=False
        watched_response = client.get(f"/api/watched/{member.id}")
        watched = watched_response.json()
        assert len(watched) == 1
        assert watched[0]["would_rewatch"] == False


class TestMovieNightMatching:
    """Test movie night matching with watched status"""

    def test_match_excludes_watched_movies(self, client, db):
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

        # Tim and Monty both swipe yes on Dune
        db.add(Swipe(member_id=tim.id, movie_id=dune.id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=monty.id, movie_id=dune.id, direction=SwipeDirection.YES))

        # Tim has watched Dune and wouldn't rewatch
        db.add(MemberWatched(member_id=tim.id, movie_id=dune.id, would_rewatch=False))
        db.commit()

        # Movie night with Tim and Monty
        response = client.post("/api/movie-night/matches", json={
            "present_member_ids": [tim.id, monty.id]
        })
        assert response.status_code == 200
        matches = response.json()["matches"]

        # Dune should NOT be a full match because Tim watched it and wouldn't rewatch
        dune_match = next((m for m in matches if m["movie"]["title"] == "Dune"), None)
        if dune_match:
            assert dune_match["is_full_match"] == False

    def test_match_includes_would_rewatch(self, client, db):
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

        # Tim and Monty both swipe yes on Dune
        db.add(Swipe(member_id=tim.id, movie_id=dune.id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=monty.id, movie_id=dune.id, direction=SwipeDirection.YES))

        # Tim has watched Dune and WOULD rewatch
        db.add(MemberWatched(member_id=tim.id, movie_id=dune.id, would_rewatch=True))
        db.commit()

        # Movie night with Tim and Monty
        response = client.post("/api/movie-night/matches", json={
            "present_member_ids": [tim.id, monty.id]
        })
        assert response.status_code == 200
        matches = response.json()["matches"]

        # Dune SHOULD be a full match because Tim would rewatch
        dune_match = next((m for m in matches if m["movie"]["title"] == "Dune"), None)
        assert dune_match is not None
        assert dune_match["is_full_match"] == True

    def test_unwatched_members_can_match(self, client, db):
        # Create members
        tim = Member(name="Tim", content_filter=ContentRating.ADULT)
        monty = Member(name="Monty", content_filter=ContentRating.ADULT)
        sally = Member(name="Sally", content_filter=ContentRating.TEEN)
        db.add_all([tim, monty, sally])
        db.commit()

        # Create movie
        dune = Movie(tmdb_id=438631, title="Dune", year=2021, content_rating=ContentRating.TEEN)
        db.add(dune)
        db.commit()

        # Add to watchlist
        db.add(WatchlistEntry(movie_id=dune.id, added_by_id=tim.id, is_active=True))
        db.commit()

        # All three swipe yes on Dune
        db.add(Swipe(member_id=tim.id, movie_id=dune.id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=monty.id, movie_id=dune.id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=sally.id, movie_id=dune.id, direction=SwipeDirection.YES))

        # Tim and Monty watched it
        db.add(MemberWatched(member_id=tim.id, movie_id=dune.id, would_rewatch=False))
        db.add(MemberWatched(member_id=monty.id, movie_id=dune.id, would_rewatch=False))
        db.commit()

        # Movie night with ONLY Sally (who hasn't watched)
        response = client.post("/api/movie-night/matches", json={
            "present_member_ids": [sally.id]
        })
        assert response.status_code == 200
        matches = response.json()["matches"]

        # Dune SHOULD match for Sally alone
        dune_match = next((m for m in matches if m["movie"]["title"] == "Dune"), None)
        assert dune_match is not None
        assert dune_match["is_full_match"] == True
