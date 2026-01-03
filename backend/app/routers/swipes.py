from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from ..database import get_db
from ..models import Swipe, Movie, Member, WatchlistEntry, SwipeDirection, MemberWatched
from ..schemas import SwipeCreate, SwipeResponse, SwipeQueueResponse, MovieResponse
from ..utils import movie_to_response

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
    """Get movies that member hasn't swiped on yet"""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Get IDs of movies already swiped (using scalar_subquery to avoid deprecation warning)
    swiped_subquery = select(Swipe.movie_id).where(
        Swipe.member_id == member_id
    ).scalar_subquery()

    # Get active watchlist movies not yet swiped, filtered by content rating
    query = db.query(Movie).join(WatchlistEntry).filter(
        WatchlistEntry.is_active == True,
        ~Movie.id.in_(swiped_subquery)
    )

    # Apply content filter based on member's setting
    from ..models import ContentRating
    if member.content_filter == ContentRating.TEEN:
        query = query.filter(Movie.content_rating.in_([ContentRating.ALL_AGES, ContentRating.TEEN]))
    elif member.content_filter == ContentRating.ALL_AGES:
        query = query.filter(Movie.content_rating == ContentRating.ALL_AGES)
    # MATURE and ADULT see everything

    movies = query.order_by(WatchlistEntry.added_at.desc()).limit(limit).all()
    total = query.count()

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
