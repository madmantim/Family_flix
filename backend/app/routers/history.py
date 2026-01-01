from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime
from ..database import get_db
from ..models import Movie, WatchHistory, WatchlistEntry
from ..schemas import WatchHistoryCreate, WatchHistoryResponse
from ..services.tmdb import TMDBService

router = APIRouter()


@router.get("/", response_model=List[WatchHistoryResponse])
def get_watch_history(
    year: int = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get watch history, optionally filtered by year"""
    query = db.query(WatchHistory)

    if year:
        query = query.filter(
            WatchHistory.watched_at >= datetime(year, 1, 1),
            WatchHistory.watched_at < datetime(year + 1, 1, 1)
        )

    entries = query.order_by(WatchHistory.watched_at.desc()).limit(limit).all()

    result = []
    for entry in entries:
        movie = entry.movie
        result.append({
            "id": entry.id,
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
                "backdrop_url": TMDBService.get_backdrop_url(movie.backdrop_path)
            },
            "watched_at": entry.watched_at,
            "watchers": entry.watchers
        })

    return result


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get watch statistics"""
    current_year = datetime.now().year

    total_watched = db.query(WatchHistory).count()

    this_year = db.query(WatchHistory).filter(
        WatchHistory.watched_at >= datetime(current_year, 1, 1)
    ).count()

    return {
        "total_watched": total_watched,
        "watched_this_year": this_year,
        "year": current_year
    }


@router.post("/", response_model=WatchHistoryResponse, status_code=201)
def mark_watched(entry: WatchHistoryCreate, db: Session = Depends(get_db)):
    """Mark a movie as watched"""
    movie = db.query(Movie).filter(Movie.id == entry.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Deactivate from watchlist
    watchlist_entries = db.query(WatchlistEntry).filter(
        WatchlistEntry.movie_id == entry.movie_id,
        WatchlistEntry.is_active == True
    ).all()

    for wl_entry in watchlist_entries:
        wl_entry.is_active = False

    # Create history entry
    history = WatchHistory(
        movie_id=entry.movie_id,
        watchers=json.dumps(entry.watcher_ids)
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return {
        "id": history.id,
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
            "backdrop_url": TMDBService.get_backdrop_url(movie.backdrop_path)
        },
        "watched_at": history.watched_at,
        "watchers": history.watchers
    }


@router.delete("/{history_id}", status_code=204)
def delete_history_entry(history_id: int, db: Session = Depends(get_db)):
    """Remove a movie from watch history"""
    entry = db.query(WatchHistory).filter(WatchHistory.id == history_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="History entry not found")

    db.delete(entry)
    db.commit()
