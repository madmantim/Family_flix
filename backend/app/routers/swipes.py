from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case
from datetime import datetime, timedelta, timezone
from typing import List
from ..database import get_db
from ..models import Swipe, Movie, Member, WatchlistEntry, SwipeDirection, MemberWatched, ContentRating
from ..schemas import SwipeCreate, SwipeResponse, SwipeQueueResponse, MovieResponse
from ..utils import movie_to_response

# Movies added within this many days are prioritized by recency
RECENCY_WINDOW_DAYS = 14

# Content rating hierarchy: a member's filter allows their level and everything below.
CONTENT_RATING_ORDER = [
    ContentRating.ALL_AGES,
    ContentRating.TEEN,
    ContentRating.MATURE,
    ContentRating.ADULT,
]


def allowed_ratings_for(member_filter: ContentRating) -> list[ContentRating]:
    """Return the list of ratings a member with this filter is allowed to see."""
    return CONTENT_RATING_ORDER[: CONTENT_RATING_ORDER.index(member_filter) + 1]

router = APIRouter()


@router.post("/", response_model=SwipeResponse, status_code=201)
def create_swipe(swipe: SwipeCreate, db: Session = Depends(get_db)):
    """Record a swipe vote"""
    # Validate member exists
    member = db.query(Member).filter(Member.id == swipe.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Validate movie exists
    movie = db.query(Movie).filter(Movie.id == swipe.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Check if already swiped - update if exists, create if not
    existing = db.query(Swipe).filter(
        Swipe.member_id == swipe.member_id,
        Swipe.movie_id == swipe.movie_id
    ).first()

    if existing:
        # Update existing swipe
        existing.direction = swipe.direction
        db_swipe = existing
    else:
        # Create new swipe
        db_swipe = Swipe(
            member_id=swipe.member_id,
            movie_id=swipe.movie_id,
            direction=swipe.direction
        )
        db.add(db_swipe)

    # If watched flag is set, create MemberWatched record if not exists
    if swipe.watched:
        existing_watched = db.query(MemberWatched).filter(
            MemberWatched.member_id == swipe.member_id,
            MemberWatched.movie_id == swipe.movie_id
        ).first()

        if not existing_watched:
            watched_record = MemberWatched(
                member_id=swipe.member_id,
                movie_id=swipe.movie_id
            )
            db.add(watched_record)

    db.commit()
    db.refresh(db_swipe)
    return db_swipe


@router.get("/queue/{member_id}", response_model=SwipeQueueResponse)
def get_swipe_queue(member_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """
    Get movies that member hasn't swiped on yet.

    Ordering priority:
    1. Movies added within RECENCY_WINDOW_DAYS: sorted by recency (newest first)
    2. Older movies: sorted by YES vote count (most popular first), then recency

    This ensures new additions get visibility while popular older movies
    don't get buried, and unpopular old movies naturally sink.
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Get IDs of movies already swiped (using scalar_subquery to avoid deprecation warning)
    swiped_subquery = select(Swipe.movie_id).where(
        Swipe.member_id == member_id
    ).scalar_subquery()

    # Calculate the recency cutoff
    recency_cutoff = datetime.now(timezone.utc) - timedelta(days=RECENCY_WINDOW_DAYS)

    # Subquery to count YES votes per movie (excluding current member's votes)
    yes_count_subquery = (
        select(Swipe.movie_id, func.count(Swipe.id).label('yes_count'))
        .where(
            Swipe.direction == SwipeDirection.YES,
            Swipe.member_id != member_id  # Don't count current member's own vote
        )
        .group_by(Swipe.movie_id)
        .subquery()
    )

    # Build main query with YES count joined
    query = (
        db.query(Movie, WatchlistEntry.added_at, func.coalesce(yes_count_subquery.c.yes_count, 0).label('yes_count'))
        .join(WatchlistEntry)
        .outerjoin(yes_count_subquery, Movie.id == yes_count_subquery.c.movie_id)
        .filter(
            WatchlistEntry.is_active == True,
            ~Movie.id.in_(swiped_subquery)
        )
    )

    # Apply content filter based on member's setting
    allowed = allowed_ratings_for(member.content_filter)
    query = query.filter(Movie.content_rating.in_(allowed))

    # Order by:
    # 1. Recent movies first (is_recent = 1 for new, 0 for old)
    # 2. Within recent: by added_at desc
    # 3. Within old: by yes_count desc, then added_at desc
    is_recent = case(
        (WatchlistEntry.added_at >= recency_cutoff, 1),
        else_=0
    )

    results = query.order_by(
        is_recent.desc(),  # Recent movies first
        case(
            (WatchlistEntry.added_at >= recency_cutoff, WatchlistEntry.added_at),
            else_=None
        ).desc().nullslast(),  # Recent: sort by date
        case(
            (WatchlistEntry.added_at < recency_cutoff, func.coalesce(yes_count_subquery.c.yes_count, 0)),
            else_=None
        ).desc().nullslast(),  # Old: sort by yes_count
        WatchlistEntry.added_at.desc()  # Final tiebreaker: recency
    ).limit(limit).all()

    # Get total count (need a simpler query for count)
    count_query = (
        db.query(func.count(Movie.id))
        .join(WatchlistEntry)
        .filter(
            WatchlistEntry.is_active == True,
            ~Movie.id.in_(swiped_subquery)
        )
    )
    count_query = count_query.filter(Movie.content_rating.in_(allowed))

    total = count_query.scalar()

    # Extract just the Movie objects for response
    movies = [row[0] for row in results]
    result = [movie_to_response(movie) for movie in movies]

    return SwipeQueueResponse(movies=result, total_unswiped=total)


@router.get("/member/{member_id}", response_model=List[SwipeResponse])
def get_member_swipes(member_id: int, db: Session = Depends(get_db)):
    """Get all swipes for a member"""
    return db.query(Swipe).filter(Swipe.member_id == member_id).all()


@router.delete("/{swipe_id}", status_code=204)
def delete_swipe(swipe_id: int, db: Session = Depends(get_db)):
    """Delete a swipe (allow re-swiping)"""
    swipe = db.query(Swipe).filter(Swipe.id == swipe_id).first()
    if not swipe:
        raise HTTPException(status_code=404, detail="Swipe not found")

    db.delete(swipe)
    db.commit()
