from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import MemberWatched, Member, Movie, WatchlistEntry, Swipe, SwipeDirection
from ..schemas import (
    MemberWatchedCreate,
    MemberWatchedResponse,
    MemberWatchedWithMovie,
    MarkWatchedRequest,
    MovieResponse,
)
from ..utils import movie_to_response

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
        result.append({
            "id": w.id,
            "movie": movie_to_response(w.movie),
            "watched_at": w.watched_at,
        })

    return result


@router.get("/history/stats")
def get_watch_stats(member_id: int = None, db: Session = Depends(get_db)):
    """Get watch statistics. If member_id provided, returns member-specific stats."""
    current_year = datetime.now().year

    if member_id:
        # Member-specific stats
        total_watched = db.query(func.count(MemberWatched.id)).filter(
            MemberWatched.member_id == member_id
        ).scalar()

        this_year = db.query(func.count(MemberWatched.id)).filter(
            MemberWatched.member_id == member_id,
            MemberWatched.watched_at >= datetime(current_year, 1, 1)
        ).scalar()
    else:
        # Global stats (count distinct movies watched)
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
    """Mark a movie as watched for multiple members and flip their votes to N"""
    # Validate movie exists
    movie = db.query(Movie).filter(Movie.id == request.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Validate all members exist
    members = db.query(Member).filter(Member.id.in_(request.member_ids)).all()
    if len(members) != len(request.member_ids):
        raise HTTPException(status_code=404, detail="One or more members not found")

    # NOTE: We no longer deactivate watchlist entries here
    # Pool membership is independent of watched state

    results = []
    for member_id in request.member_ids:
        # Create or update watched record
        existing = db.query(MemberWatched).filter(
            MemberWatched.member_id == member_id,
            MemberWatched.movie_id == request.movie_id
        ).first()

        if existing:
            # Already watched, just return it
            results.append(existing)
        else:
            # Create new record
            watched = MemberWatched(
                member_id=member_id,
                movie_id=request.movie_id
            )
            db.add(watched)
            db.flush()  # Get ID without committing
            results.append(watched)

        # Flip swipe to NO for this member (they just watched it)
        existing_swipe = db.query(Swipe).filter(
            Swipe.member_id == member_id,
            Swipe.movie_id == request.movie_id
        ).first()

        if existing_swipe:
            existing_swipe.direction = SwipeDirection.NO
        else:
            # Create NO swipe if none exists
            new_swipe = Swipe(
                member_id=member_id,
                movie_id=request.movie_id,
                direction=SwipeDirection.NO
            )
            db.add(new_swipe)

    # Single commit for all changes
    db.commit()
    for r in results:
        db.refresh(r)

    return results


@router.get("/{member_id}", response_model=List[MemberWatchedWithMovie])
def get_member_watched(member_id: int, limit: int = None, db: Session = Depends(get_db)):
    """Get all movies a member has watched"""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    query = db.query(MemberWatched).filter(
        MemberWatched.member_id == member_id
    ).order_by(MemberWatched.watched_at.desc())

    if limit:
        query = query.limit(limit)

    watched = query.all()

    result = []
    for w in watched:
        result.append({
            "id": w.id,
            "movie": movie_to_response(w.movie),
            "watched_at": w.watched_at,
        })

    return result


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
        movie_id=movie_id
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
