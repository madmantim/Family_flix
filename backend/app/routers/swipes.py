from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Swipe, Movie, Member, WatchlistEntry, SwipeDirection, MemberWatched
from ..schemas import SwipeCreate, SwipeResponse, SwipeQueueResponse, MovieResponse
from ..services.tmdb import TMDBService

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

    # Check if already swiped
    existing = db.query(Swipe).filter(
        Swipe.member_id == swipe.member_id,
        Swipe.movie_id == swipe.movie_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already swiped on this movie")

    # Create swipe
    db_swipe = Swipe(
        member_id=swipe.member_id,
        movie_id=swipe.movie_id,
        direction=swipe.direction
    )
    db.add(db_swipe)

    # If watched flag is set, create/update MemberWatched record
    if swipe.watched:
        would_rewatch = swipe.direction == SwipeDirection.YES
        existing_watched = db.query(MemberWatched).filter(
            MemberWatched.member_id == swipe.member_id,
            MemberWatched.movie_id == swipe.movie_id
        ).first()

        if existing_watched:
            existing_watched.would_rewatch = would_rewatch
        else:
            watched_record = MemberWatched(
                member_id=swipe.member_id,
                movie_id=swipe.movie_id,
                would_rewatch=would_rewatch
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

    # Get IDs of movies already swiped
    swiped_ids = db.query(Swipe.movie_id).filter(Swipe.member_id == member_id).subquery()

    # Get active watchlist movies not yet swiped, filtered by content rating
    query = db.query(Movie).join(WatchlistEntry).filter(
        WatchlistEntry.is_active == True,
        ~Movie.id.in_(swiped_ids)
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

    result = []
    for movie in movies:
        result.append({
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
        })

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
