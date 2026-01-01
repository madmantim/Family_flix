from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import MemberWatched, Member, Movie
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


@router.delete("/{member_id}/{movie_id}", status_code=204)
def remove_watched(member_id: int, movie_id: int, db: Session = Depends(get_db)):
    """Remove watched status for a member (rarely used)"""
    watched = db.query(MemberWatched).filter(
        MemberWatched.member_id == member_id,
        MemberWatched.movie_id == movie_id
    ).first()

    if not watched:
        raise HTTPException(status_code=404, detail="Watched record not found")

    db.delete(watched)
    db.commit()
