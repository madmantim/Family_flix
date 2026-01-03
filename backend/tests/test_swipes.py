import pytest
from app.models import Member, Movie, WatchlistEntry, ContentRating


def test_swipe_queue_returns_unswiped_movies(client, db):
    """Test that swipe queue only returns movies not yet swiped"""
    # Create member
    member = Member(name="Tim", content_filter=ContentRating.ADULT)
    db.add(member)
    db.commit()

    # Create movies
    movie1 = Movie(tmdb_id=123, title="Movie 1", content_rating=ContentRating.ALL_AGES)
    movie2 = Movie(tmdb_id=456, title="Movie 2", content_rating=ContentRating.ALL_AGES)
    db.add_all([movie1, movie2])
    db.commit()

    # Add to watchlist
    db.add(WatchlistEntry(movie_id=movie1.id, added_by_id=member.id))
    db.add(WatchlistEntry(movie_id=movie2.id, added_by_id=member.id))
    db.commit()

    # Get queue - should have 2 movies
    resp = client.get(f"/api/swipes/queue/{member.id}")
    assert resp.status_code == 200
    assert resp.json()["total_unswiped"] == 2

    # Swipe on movie1
    client.post("/api/swipes/", json={
        "member_id": member.id,
        "movie_id": movie1.id,
        "direction": "yes"
    })

    # Get queue again - should have 1 movie
    resp = client.get(f"/api/swipes/queue/{member.id}")
    assert resp.json()["total_unswiped"] == 1
    assert resp.json()["movies"][0]["title"] == "Movie 2"


def test_swipe_queue_filters_by_content_rating(client, db):
    """Test that teen members don't see adult content"""
    # Create teen member
    teen = Member(name="Monty", content_filter=ContentRating.TEEN)
    db.add(teen)
    db.commit()

    # Create movies with different ratings
    kid_movie = Movie(tmdb_id=123, title="Kid Movie", content_rating=ContentRating.ALL_AGES)
    teen_movie = Movie(tmdb_id=456, title="Teen Movie", content_rating=ContentRating.TEEN)
    adult_movie = Movie(tmdb_id=789, title="Adult Movie", content_rating=ContentRating.ADULT)
    db.add_all([kid_movie, teen_movie, adult_movie])
    db.commit()

    # Add all to watchlist
    for movie in [kid_movie, teen_movie, adult_movie]:
        db.add(WatchlistEntry(movie_id=movie.id, added_by_id=teen.id))
    db.commit()

    # Get queue for teen
    resp = client.get(f"/api/swipes/queue/{teen.id}")
    assert resp.status_code == 200

    # Should only see kid and teen movies
    movies = resp.json()["movies"]
    titles = [m["title"] for m in movies]
    assert "Kid Movie" in titles
    assert "Teen Movie" in titles
    assert "Adult Movie" not in titles


def test_swipe_updates_existing(client, db):
    """Test that swiping again updates the existing swipe"""
    # Create member and movie
    member = Member(name="Tim", content_filter=ContentRating.ADULT)
    db.add(member)
    movie = Movie(tmdb_id=123, title="Test Movie", content_rating=ContentRating.ALL_AGES)
    db.add(movie)
    db.commit()

    # First swipe - NO
    resp1 = client.post("/api/swipes/", json={
        "member_id": member.id,
        "movie_id": movie.id,
        "direction": "no"
    })
    assert resp1.status_code == 201
    assert resp1.json()["direction"] == "no"

    # Second swipe - should update to YES
    resp2 = client.post("/api/swipes/", json={
        "member_id": member.id,
        "movie_id": movie.id,
        "direction": "yes"
    })
    assert resp2.status_code == 201
    assert resp2.json()["direction"] == "yes"

    # Should still only have one swipe (updated, not duplicated)
    swipes = client.get(f"/api/swipes/member/{member.id}")
    assert len(swipes.json()) == 1
    assert swipes.json()[0]["direction"] == "yes"


def test_swipe_invalid_member(client, db):
    """Test swiping with invalid member returns 404"""
    movie = Movie(tmdb_id=123, title="Test", content_rating=ContentRating.ALL_AGES)
    db.add(movie)
    db.commit()

    resp = client.post("/api/swipes/", json={
        "member_id": 999,
        "movie_id": movie.id,
        "direction": "yes"
    })
    assert resp.status_code == 404


def test_swipe_invalid_movie(client, db):
    """Test swiping with invalid movie returns 404"""
    member = Member(name="Tim", content_filter=ContentRating.ADULT)
    db.add(member)
    db.commit()

    resp = client.post("/api/swipes/", json={
        "member_id": member.id,
        "movie_id": 999,
        "direction": "yes"
    })
    assert resp.status_code == 404
