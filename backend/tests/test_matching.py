import pytest
from app.models import Member, Movie, Swipe, WatchlistEntry, SwipeDirection, ContentRating


def test_full_match_calculation(client, db):
    """Test that movies with YES from all present members are full matches"""
    # Create members
    member1 = Member(name="Tim", content_filter=ContentRating.ADULT)
    member2 = Member(name="Sarah", content_filter=ContentRating.ADULT)
    db.add_all([member1, member2])
    db.commit()

    # Create movie
    movie = Movie(tmdb_id=123, title="Test Movie", content_rating=ContentRating.ALL_AGES)
    db.add(movie)
    db.commit()

    # Add to watchlist
    entry = WatchlistEntry(movie_id=movie.id, added_by_id=member1.id)
    db.add(entry)

    # Both swipe yes
    db.add(Swipe(member_id=member1.id, movie_id=movie.id, direction=SwipeDirection.YES))
    db.add(Swipe(member_id=member2.id, movie_id=movie.id, direction=SwipeDirection.YES))
    db.commit()

    # Get matches
    response = client.post(
        "/api/movie-night/matches",
        json={"present_member_ids": [member1.id, member2.id]}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["matches"]) == 1
    assert data["matches"][0]["is_full_match"] is True
    assert data["matches"][0]["yes_votes"] == 2


def test_partial_match_calculation(client, db):
    """Test partial matches when not everyone voted yes"""
    # Create members
    member1 = Member(name="Tim", content_filter=ContentRating.ADULT)
    member2 = Member(name="Sarah", content_filter=ContentRating.ADULT)
    member3 = Member(name="Monty", content_filter=ContentRating.TEEN)
    db.add_all([member1, member2, member3])
    db.commit()

    # Create movie
    movie = Movie(tmdb_id=123, title="Test Movie", content_rating=ContentRating.ALL_AGES)
    db.add(movie)
    db.commit()

    # Add to watchlist
    entry = WatchlistEntry(movie_id=movie.id, added_by_id=member1.id)
    db.add(entry)

    # 2 out of 3 swipe yes
    db.add(Swipe(member_id=member1.id, movie_id=movie.id, direction=SwipeDirection.YES))
    db.add(Swipe(member_id=member2.id, movie_id=movie.id, direction=SwipeDirection.YES))
    db.add(Swipe(member_id=member3.id, movie_id=movie.id, direction=SwipeDirection.NO))
    db.commit()

    # Get matches
    response = client.post(
        "/api/movie-night/matches",
        json={"present_member_ids": [member1.id, member2.id, member3.id]}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["matches"]) == 1
    assert data["matches"][0]["is_full_match"] is False
    assert data["matches"][0]["yes_votes"] == 2
    assert data["matches"][0]["total_present"] == 3


def test_content_filtering(client, db):
    """Test that mature content is filtered for teen members"""
    # Create adult and teen members
    adult = Member(name="Tim", content_filter=ContentRating.ADULT)
    teen = Member(name="Monty", content_filter=ContentRating.TEEN)
    db.add_all([adult, teen])
    db.commit()

    # Create adult movie
    adult_movie = Movie(tmdb_id=123, title="Adult Movie", content_rating=ContentRating.ADULT)
    kid_movie = Movie(tmdb_id=456, title="Kid Movie", content_rating=ContentRating.ALL_AGES)
    db.add_all([adult_movie, kid_movie])
    db.commit()

    # Add to watchlist
    db.add(WatchlistEntry(movie_id=adult_movie.id, added_by_id=adult.id))
    db.add(WatchlistEntry(movie_id=kid_movie.id, added_by_id=adult.id))

    # Both swipe yes on both
    for movie in [adult_movie, kid_movie]:
        db.add(Swipe(member_id=adult.id, movie_id=movie.id, direction=SwipeDirection.YES))
        db.add(Swipe(member_id=teen.id, movie_id=movie.id, direction=SwipeDirection.YES))
    db.commit()

    # Get matches with teen present - adult movie should be filtered
    response = client.post(
        "/api/movie-night/matches",
        json={"present_member_ids": [adult.id, teen.id]}
    )

    assert response.status_code == 200
    data = response.json()
    # Only kid movie should appear
    assert len(data["matches"]) == 1
    assert data["matches"][0]["movie"]["title"] == "Kid Movie"


def test_matches_sorted_by_votes(client, db):
    """Test that matches are sorted by vote count"""
    # Create 3 members
    members = [Member(name=f"Member{i}", content_filter=ContentRating.ADULT) for i in range(3)]
    db.add_all(members)
    db.commit()

    # Create 2 movies
    movie1 = Movie(tmdb_id=123, title="Movie 1", content_rating=ContentRating.ALL_AGES)
    movie2 = Movie(tmdb_id=456, title="Movie 2", content_rating=ContentRating.ALL_AGES)
    db.add_all([movie1, movie2])
    db.commit()

    # Add to watchlist
    db.add(WatchlistEntry(movie_id=movie1.id, added_by_id=members[0].id))
    db.add(WatchlistEntry(movie_id=movie2.id, added_by_id=members[0].id))
    db.commit()

    # Movie 1: 2 yes votes
    db.add(Swipe(member_id=members[0].id, movie_id=movie1.id, direction=SwipeDirection.YES))
    db.add(Swipe(member_id=members[1].id, movie_id=movie1.id, direction=SwipeDirection.YES))

    # Movie 2: 3 yes votes (full match)
    for m in members:
        db.add(Swipe(member_id=m.id, movie_id=movie2.id, direction=SwipeDirection.YES))
    db.commit()

    response = client.post(
        "/api/movie-night/matches",
        json={"present_member_ids": [m.id for m in members]}
    )

    data = response.json()
    # Full match should be first
    assert data["matches"][0]["movie"]["title"] == "Movie 2"
    assert data["matches"][0]["is_full_match"] is True


def test_runoff_voting(client, db):
    """Test the runoff voting flow"""
    # Create members
    member1 = Member(name="Tim", content_filter=ContentRating.ADULT)
    member2 = Member(name="Sarah", content_filter=ContentRating.ADULT)
    db.add_all([member1, member2])
    db.commit()

    # Create movie
    movie = Movie(tmdb_id=123, title="Test Movie", content_rating=ContentRating.ALL_AGES)
    db.add(movie)
    db.commit()

    # Start runoff
    start_resp = client.post(
        "/api/movie-night/start-runoff",
        json={"present_member_ids": [member1.id, member2.id]}
    )
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]

    # Cast votes
    client.post(f"/api/movie-night/vote/{session_id}", json={
        "member_id": member1.id,
        "movie_id": movie.id
    })
    client.post(f"/api/movie-night/vote/{session_id}", json={
        "member_id": member2.id,
        "movie_id": movie.id
    })

    # Get result
    result_resp = client.post(f"/api/movie-night/result/{session_id}")
    assert result_resp.status_code == 200
    data = result_resp.json()
    assert data["winner"]["title"] == "Test Movie"
    assert data["was_tie"] is False
