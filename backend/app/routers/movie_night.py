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

    Matching logic:
    1. Full matches: Everyone present voted YES
    2. Partial matches: Most present members voted YES
    3. Ranked by source priority (manual > curated > trending) then recency
    """
    if len(request.present_member_ids) < 1:
        raise HTTPException(status_code=400, detail="At least one member must be present")

    # Validate all members exist
    members = db.query(Member).filter(Member.id.in_(request.present_member_ids)).all()
    if len(members) != len(request.present_member_ids):
        raise HTTPException(status_code=404, detail="One or more members not found")

    member_ids = request.present_member_ids

    # Determine the most restrictive content filter for present members
    content_filters = [m.content_filter for m in members]
    # Order: ALL_AGES < TEEN < MATURE < ADULT
    filter_order = [ContentRating.ALL_AGES, ContentRating.TEEN, ContentRating.MATURE, ContentRating.ADULT]
    min_filter = min(content_filters, key=lambda x: filter_order.index(x))

    # Get all active watchlist movies
    active_movies = db.query(Movie).join(WatchlistEntry).filter(
        WatchlistEntry.is_active == True
    ).all()

    # Filter by content rating
    allowed_ratings = filter_order[:filter_order.index(min_filter) + 1]
    filtered_movies = [m for m in active_movies if m.content_rating in allowed_ratings]

    # Calculate yes votes for each movie from present members
    matches = []

    # Create a lookup dict for members by id
    members_by_id = {m.id: m for m in members}

    for movie in filtered_movies:
        # Get yes swipes from present members
        yes_swipes = db.query(Swipe).filter(
            Swipe.movie_id == movie.id,
            Swipe.member_id.in_(member_ids),
            Swipe.direction == SwipeDirection.YES
        ).all()

        yes_member_ids = {s.member_id for s in yes_swipes}
        yes_voters = [members_by_id[mid] for mid in yes_member_ids if mid in members_by_id]

        # Check eligibility: member is eligible if not watched OR would_rewatch=True
        eligible_count = 0
        any_blocked = False  # True if any member watched and wouldn't rewatch

        for mid in member_ids:
            watched = db.query(MemberWatched).filter(
                MemberWatched.member_id == mid,
                MemberWatched.movie_id == movie.id
            ).first()

            if watched is None:
                # Not watched = eligible (count if they swiped yes)
                if mid in yes_member_ids:
                    eligible_count += 1
            elif watched.would_rewatch:
                # Watched but would rewatch = eligible (count if they swiped yes)
                if mid in yes_member_ids:
                    eligible_count += 1
            else:
                # Watched and would not rewatch = blocked
                any_blocked = True
                break

        # Skip movies where any present member has watched and wouldn't rewatch
        if any_blocked:
            continue

        # Only include if all present members are eligible and swiped yes
        all_eligible = eligible_count == len(member_ids)

        # Get watchlist entry for source info
        entry = db.query(WatchlistEntry).filter(
            WatchlistEntry.movie_id == movie.id,
            WatchlistEntry.is_active == True
        ).first()

        matches.append({
            "movie": movie,
            "yes_votes": eligible_count,
            "total_present": len(member_ids),
            "is_full_match": all_eligible,
            "source": entry.source if entry else "manual",
            "added_at": entry.added_at if entry else None,
            "voters": yes_voters
        })

    # Sort: full matches first, then by yes_votes desc, then by source priority, then recency (newest first)
    source_priority = {"manual": 0, "curated": 1, "trending": 2}
    matches.sort(key=lambda m: (
        -int(m["is_full_match"]),  # Full matches first
        -m["yes_votes"],  # Most votes
        source_priority.get(m["source"], 3),  # Source priority
        -(m["added_at"].timestamp() if m["added_at"] else 0)  # Newest first
    ))

    # Return all matches (no limit)
    top_matches = matches

    result = []
    for m in top_matches:
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
