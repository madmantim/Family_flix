from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Movie, Member, Swipe, WatchlistEntry, SwipeDirection, ContentRating, MemberWatched
from ..schemas import MovieNightRequest, MovieNightResponse, MatchedMovie
from ..utils import movie_to_response

router = APIRouter()


@router.post("/matches", response_model=MovieNightResponse)
def get_matches(request: MovieNightRequest, db: Session = Depends(get_db)):
    """
    Calculate movie matches for present members.

    Ranking (simplified):
    1. Y count (descending) - more yes votes = better
    2. N(W) count (ascending) - fewer watched among N voters = fresher
    3. Recency (newest first) - tiebreaker
    """
    if len(request.present_member_ids) < 1:
        raise HTTPException(status_code=400, detail="At least one member must be present")

    # Validate all members exist
    members = db.query(Member).filter(Member.id.in_(request.present_member_ids)).all()
    if len(members) != len(request.present_member_ids):
        raise HTTPException(status_code=404, detail="One or more members not found")

    member_ids = request.present_member_ids
    members_by_id = {m.id: m for m in members}

    # Get all members to identify absent ones
    all_members = db.query(Member).all()
    absent_member_ids = [m.id for m in all_members if m.id not in member_ids]
    absent_members_by_id = {m.id: m for m in all_members if m.id in absent_member_ids}

    # Determine the most restrictive content filter for present members
    content_filters = [m.content_filter for m in members]
    filter_order = [ContentRating.ALL_AGES, ContentRating.TEEN, ContentRating.MATURE, ContentRating.ADULT]
    min_filter = min(content_filters, key=lambda x: filter_order.index(x))

    # Get all active watchlist entries with movies
    active_entries = db.query(WatchlistEntry).filter(
        WatchlistEntry.is_active == True
    ).all()

    movie_ids = [e.movie_id for e in active_entries]
    active_movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all() if movie_ids else []
    movies_by_id = {m.id: m for m in active_movies}
    entries_by_movie_id = {e.movie_id: e for e in active_entries}

    # Filter by content rating
    allowed_ratings = filter_order[:filter_order.index(min_filter) + 1]
    filtered_movies = [m for m in active_movies if m.content_rating in allowed_ratings]
    filtered_movie_ids = [m.id for m in filtered_movies]

    # Batch-load all YES swipes from present members for filtered movies
    all_yes_swipes = db.query(Swipe).filter(
        Swipe.movie_id.in_(filtered_movie_ids),
        Swipe.member_id.in_(member_ids),
        Swipe.direction == SwipeDirection.YES
    ).all() if filtered_movie_ids else []

    # Build lookup: movie_id -> set of member_ids who voted YES
    yes_by_movie = {}
    for swipe in all_yes_swipes:
        if swipe.movie_id not in yes_by_movie:
            yes_by_movie[swipe.movie_id] = set()
        yes_by_movie[swipe.movie_id].add(swipe.member_id)

    # Batch-load YES swipes from absent members for filtered movies
    absent_yes_swipes = db.query(Swipe).filter(
        Swipe.movie_id.in_(filtered_movie_ids),
        Swipe.member_id.in_(absent_member_ids),
        Swipe.direction == SwipeDirection.YES
    ).all() if filtered_movie_ids and absent_member_ids else []

    # Build lookup: movie_id -> set of absent member_ids who voted YES
    absent_yes_by_movie = {}
    for swipe in absent_yes_swipes:
        if swipe.movie_id not in absent_yes_by_movie:
            absent_yes_by_movie[swipe.movie_id] = set()
        absent_yes_by_movie[swipe.movie_id].add(swipe.member_id)

    # Batch-load all watched records for present members
    all_watched = db.query(MemberWatched).filter(
        MemberWatched.movie_id.in_(filtered_movie_ids),
        MemberWatched.member_id.in_(member_ids)
    ).all() if filtered_movie_ids else []

    # Build lookup: movie_id -> set of member_ids who watched
    watched_by_movie = {}
    for w in all_watched:
        if w.movie_id not in watched_by_movie:
            watched_by_movie[w.movie_id] = set()
        watched_by_movie[w.movie_id].add(w.member_id)

    matches = []

    for movie in filtered_movies:
        # Get yes swipes from present members (from pre-loaded data)
        yes_member_ids = yes_by_movie.get(movie.id, set())
        yes_voters = [members_by_id[mid] for mid in yes_member_ids if mid in members_by_id]
        y_count = len(yes_member_ids)

        # Get yes swipes from absent members
        absent_yes_member_ids = absent_yes_by_movie.get(movie.id, set())
        absent_yes_voters = [absent_members_by_id[mid] for mid in absent_yes_member_ids if mid in absent_members_by_id]

        # Count N(W) - members who voted NO (or didn't vote YES) AND have watched
        watched_member_ids = watched_by_movie.get(movie.id, set())
        n_watched_count = sum(1 for mid in member_ids if mid not in yes_member_ids and mid in watched_member_ids)

        # Get watchlist entry for recency (from pre-loaded data)
        entry = entries_by_movie_id.get(movie.id)

        matches.append({
            "movie": movie,
            "yes_votes": y_count,
            "total_present": len(member_ids),
            "is_full_match": y_count == len(member_ids),
            "n_watched_count": n_watched_count,
            "added_at": entry.added_at if entry else None,
            "voters": yes_voters,
            "absent_yes_voters": absent_yes_voters
        })

    # Sort: Y count desc, N(W) count asc, recency desc
    matches.sort(key=lambda m: (
        -m["yes_votes"],
        m["n_watched_count"],
        -(m["added_at"].timestamp() if m["added_at"] else 0)
    ))

    result = []
    for m in matches:
        result.append(MatchedMovie(
            movie=movie_to_response(m["movie"]),
            yes_votes=m["yes_votes"],
            total_present=m["total_present"],
            is_full_match=m["is_full_match"],
            voters=[{
                "id": v.id,
                "name": v.name,
                "avatar_url": v.avatar_url,
                "content_filter": v.content_filter,
                "created_at": v.created_at
            } for v in m["voters"]],
            absent_yes_voters=[{
                "id": v.id,
                "name": v.name,
                "avatar_url": v.avatar_url,
                "content_filter": v.content_filter,
                "created_at": v.created_at
            } for v in m["absent_yes_voters"]]
        ))

    return MovieNightResponse(
        matches=result,
        present_members=members
    )
