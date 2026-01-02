from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import MemberWatched, Member, Movie, WatchlistEntry
from ..schemas import (
    MemberWatchedCreate,
    MemberWatchedUpdate,
    MemberWatchedResponse,
    MemberWatchedWithMovie,
    MarkWatchedRequest,
    MovieResponse,
)
from ..services.tmdb import TMDBService

router = APIRouter()


# IMPORTANT: Specific routes must come BEFORE wildcard routes like /{member_id}

@router.get("/history/all", response_model=List[MemberWatchedWithMovie])
def get_all_watched_history(
    year: int = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get watch history across all members (deduplicated by movie).
    Returns the earliest watch date for each movie.
    """
    # Subquery to get earliest watch date per movie
    subquery = db.query(
        MemberWatched.movie_id,
        func.min(MemberWatched.watched_at).label('first_watched')
    ).group_by(MemberWatched.movie_id).subquery()

    # Join to get full movie details
    query = db.query(MemberWatched).join(
        subquery,
        (MemberWatched.movie_id == subquery.c.movie_id) &
        (MemberWatched.watched_at == subquery.c.first_watched)
    )

    if year:
        query = query.filter(
            MemberWatched.watched_at >= datetime(year, 1, 1),
            MemberWatched.watched_at < datetime(year + 1, 1, 1)
        )

    entries = query.order_by(MemberWatched.watched_at.desc()).limit(limit).all()

    result = []
    for w in entries:
        movie = w.movie
        result.append({
            "id": w.id,
            "movie": {
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
                "backdrop_url": TMDBService.get_backdrop_url(movie.backdrop_path),
            },
            "watched_at": w.watched_at,
            "would_rewatch": w.would_rewatch,
        })

    return result


@router.get("/history/stats")
def get_watch_stats(db: Session = Depends(get_db)):
    """Get watch statistics derived from per-member watched records"""
    current_year = datetime.now().year

    # Count distinct movies watched (not individual member records)
    total_watched = db.query(func.count(func.distinct(MemberWatched.movie_id))).scalar()

    this_year = db.query(func.count(func.distinct(MemberWatched.movie_id))).filter(
        MemberWatched.watched_at >= datetime(current_year, 1, 1)
    ).scalar()

    return {
        "total_watched": total_watched or 0,
        "watched_this_year": this_year or 0,
        "year": current_year
    }


@router.post("/", response_model=List[MemberWatchedResponse])
def mark_watched(request: MarkWatchedRequest, db: Session = Depends(get_db)):
    """Mark a movie as watched for multiple members"""
    # Validate movie exists
    movie = db.query(Movie).filter(Movie.id == request.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Validate all members exist
    members = db.query(Member).filter(Member.id.in_(request.member_ids)).all()
    if len(members) != len(request.member_ids):
        raise HTTPException(status_code=404, detail="One or more members not found")

    # Deactivate watchlist entries for this movie
    watchlist_entries = db.query(WatchlistEntry).filter(
        WatchlistEntry.movie_id == request.movie_id,
        WatchlistEntry.is_active == True
    ).all()
    for entry in watchlist_entries:
        entry.is_active = False

    results = []
    for member_id in request.member_ids:
        # Check if already watched
        existing = db.query(MemberWatched).filter(
            MemberWatched.member_id == member_id,
            MemberWatched.movie_id == request.movie_id
        ).first()

        if existing:
            # Update would_rewatch if already exists
            existing.would_rewatch = request.would_rewatch
            db.commit()
            db.refresh(existing)
            results.append(existing)
        else:
            # Create new record
            watched = MemberWatched(
                member_id=member_id,
                movie_id=request.movie_id,
                would_rewatch=request.would_rewatch
            )
            db.add(watched)
            db.commit()
            db.refresh(watched)
            results.append(watched)

    return results


@router.get("/{member_id}", response_model=List[MemberWatchedWithMovie])
def get_member_watched(member_id: int, db: Session = Depends(get_db)):
    """Get all movies a member has watched"""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    watched = db.query(MemberWatched).filter(
        MemberWatched.member_id == member_id
    ).order_by(MemberWatched.watched_at.desc()).all()

    result = []
    for w in watched:
        movie = w.movie
        result.append({
            "id": w.id,
            "movie": {
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
                "backdrop_url": TMDBService.get_backdrop_url(movie.backdrop_path),
            },
            "watched_at": w.watched_at,
            "would_rewatch": w.would_rewatch,
        })

    return result


@router.patch("/{member_id}/{movie_id}", response_model=MemberWatchedResponse)
def update_would_rewatch(
    member_id: int,
    movie_id: int,
    update: MemberWatchedUpdate,
    db: Session = Depends(get_db)
):
    """Update would_rewatch status for a member's watched movie"""
    watched = db.query(MemberWatched).filter(
        MemberWatched.member_id == member_id,
        MemberWatched.movie_id == movie_id
    ).first()

    if not watched:
        raise HTTPException(status_code=404, detail="Watched record not found")

    watched.would_rewatch = update.would_rewatch
    db.commit()
    db.refresh(watched)

    return watched


@router.put("/{member_id}/{movie_id}", response_model=MemberWatchedResponse)
def toggle_watched(member_id: int, movie_id: int, db: Session = Depends(get_db)):
    """
    Simple watched toggle - marks movie as watched for a member.
    No side effects (doesn't affect watchlist or swipes).
    Use DELETE to unmark.
    """
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Check if already watched
    existing = db.query(MemberWatched).filter(
        MemberWatched.member_id == member_id,
        MemberWatched.movie_id == movie_id
    ).first()

    if existing:
        return existing

    # Create new watched record (no side effects)
    watched = MemberWatched(
        member_id=member_id,
        movie_id=movie_id,
        would_rewatch=False
    )
    db.add(watched)
    db.commit()
    db.refresh(watched)

    return watched


@router.delete("/{member_id}/{movie_id}", status_code=204)
def remove_watched(member_id: int, movie_id: int, db: Session = Depends(get_db)):
    """Remove watched status for a member"""
    watched = db.query(MemberWatched).filter(
        MemberWatched.member_id == member_id,
        MemberWatched.movie_id == movie_id
    ).first()

    if not watched:
        raise HTTPException(status_code=404, detail="Watched record not found")

    db.delete(watched)
    db.commit()
