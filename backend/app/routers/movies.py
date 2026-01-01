from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Movie
from ..schemas import MovieResponse, TMDBSearchResponse, TMDBSearchResult
from ..services.tmdb import get_tmdb_service, TMDBService

router = APIRouter()


@router.get("/search", response_model=TMDBSearchResponse)
async def search_movies(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    tmdb: TMDBService = Depends(get_tmdb_service)
):
    """Search TMDB for movies"""
    results = await tmdb.search_movies(query, page)

    return TMDBSearchResponse(
        results=[
            TMDBSearchResult(
                tmdb_id=m["id"],
                title=m["title"],
                year=int(m["release_date"][:4]) if m.get("release_date") else None,
                overview=m.get("overview"),
                poster_url=tmdb.get_poster_url(m.get("poster_path")),
                vote_average=m.get("vote_average")
            )
            for m in results.get("results", [])
        ],
        page=results.get("page", 1),
        total_pages=results.get("total_pages", 0),
        total_results=results.get("total_results", 0)
    )


@router.get("/trending", response_model=TMDBSearchResponse)
async def get_trending(
    page: int = Query(1, ge=1),
    tmdb: TMDBService = Depends(get_tmdb_service)
):
    """Get trending movies from TMDB"""
    results = await tmdb.get_trending("week", page)

    return TMDBSearchResponse(
        results=[
            TMDBSearchResult(
                tmdb_id=m["id"],
                title=m["title"],
                year=int(m["release_date"][:4]) if m.get("release_date") else None,
                overview=m.get("overview"),
                poster_url=tmdb.get_poster_url(m.get("poster_path")),
                vote_average=m.get("vote_average")
            )
            for m in results.get("results", [])
        ],
        page=results.get("page", 1),
        total_pages=results.get("total_pages", 0),
        total_results=results.get("total_results", 0)
    )


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    """Get a movie from local database"""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    from ..services.tmdb import TMDBService
    movie_dict = {
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
        "created_at": movie.created_at,
        "poster_url": TMDBService.get_poster_url(movie.poster_path),
        "backdrop_url": TMDBService.get_backdrop_url(movie.backdrop_path)
    }
    return movie_dict


@router.get("/", response_model=List[MovieResponse])
def get_all_movies(db: Session = Depends(get_db)):
    """Get all movies in the local database"""
    movies = db.query(Movie).all()
    from ..services.tmdb import TMDBService

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
            "created_at": movie.created_at,
            "poster_url": TMDBService.get_poster_url(movie.poster_path),
            "backdrop_url": TMDBService.get_backdrop_url(movie.backdrop_path)
        })
    return result
