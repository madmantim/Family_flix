from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Movie, Member, Swipe, WatchlistEntry, SwipeDirection, ContentRating, MemberWatched
from ..schemas import MovieNightRequest, MovieNightResponse, MatchedMovie
from ..services.tmdb import TMDBService

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

    # Determine the most restrictive content filter for present members
    content_filters = [m.content_filter for m in members]
    filter_order = [ContentRating.ALL_AGES, ContentRating.TEEN, ContentRating.MATURE, ContentRating.ADULT]
    min_filter = min(content_filters, key=lambda x: filter_order.index(x))

    # Get all active watchlist movies
    active_movies = db.query(Movie).join(WatchlistEntry).filter(
        WatchlistEntry.is_active == True
    ).all()

    # Filter by content rating
    allowed_ratings = filter_order[:filter_order.index(min_filter) + 1]
    filtered_movies = [m for m in active_movies if m.content_rating in allowed_ratings]

    matches = []

    for movie in filtered_movies:
        # Get yes swipes from present members
        yes_swipes = db.query(Swipe).filter(
            Swipe.movie_id == movie.id,
            Swipe.member_id.in_(member_ids),
            Swipe.direction == SwipeDirection.YES
        ).all()

        yes_member_ids = {s.member_id for s in yes_swipes}
        yes_voters = [members_by_id[mid] for mid in yes_member_ids if mid in members_by_id]
        y_count = len(yes_member_ids)

        # Count N(W) - members who voted NO (or didn't vote YES) AND have watched
        n_watched_count = 0
        for mid in member_ids:
            if mid not in yes_member_ids:
                # This member didn't vote YES - check if they've watched
                watched = db.query(MemberWatched).filter(
                    MemberWatched.member_id == mid,
                    MemberWatched.movie_id == movie.id
                ).first()
                if watched:
                    n_watched_count += 1

        # Get watchlist entry for recency
        entry = db.query(WatchlistEntry).filter(
            WatchlistEntry.movie_id == movie.id,
            WatchlistEntry.is_active == True
        ).first()

        matches.append({
            "movie": movie,
            "yes_votes": y_count,
            "total_present": len(member_ids),
            "is_full_match": y_count == len(member_ids),
            "n_watched_count": n_watched_count,
            "added_at": entry.added_at if entry else None,
            "voters": yes_voters
        })

    # Sort: Y count desc, N(W) count asc, recency desc
    matches.sort(key=lambda m: (
        -m["yes_votes"],
        m["n_watched_count"],
        -(m["added_at"].timestamp() if m["added_at"] else 0)
    ))

    result = []
    for m in matches:
        movie = m["movie"]
        result.append(MatchedMovie(
            movie={
                "id": movie.id,
                "tmdb_id": movie.tmdb_id,
                "title": movie.title,
                "year": movie.year,
                "overview": movie.overview,
                "poster_path": movie.poster_path,
                "backdrop_path": movie.backdrop_path,
                "vote_average": movie.vote_average,
                "content_rating": movie.content_rating,
                "runtime": movie.runtime,
                "genres": movie.genres,
                "imdb_id": movie.imdb_id,
                "rt_critic_score": movie.rt_critic_score,
                "rt_audience_score": movie.rt_audience_score,
                "rt_url": movie.rt_url,
                "trailer_url": movie.trailer_url,
                "created_at": movie.created_at,
                "poster_url": TMDBService.get_poster_url(movie.poster_path),
                "backdrop_url": TMDBService.get_backdrop_url(movie.backdrop_path)
            },
            yes_votes=m["yes_votes"],
            total_present=m["total_present"],
            is_full_match=m["is_full_match"],
            voters=[{
                "id": v.id,
                "name": v.name,
                "avatar_url": v.avatar_url,
                "content_filter": v.content_filter,
                "created_at": v.created_at
            } for v in m["voters"]]
        ))

    return MovieNightResponse(
        matches=result,
        present_members=members
    )
