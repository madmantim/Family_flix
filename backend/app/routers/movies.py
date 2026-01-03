from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Literal, Optional
from datetime import datetime, timedelta
from ..database import get_db
from ..models import Movie
from ..schemas import MovieResponse, TMDBSearchResponse, TMDBSearchResult
from ..services.tmdb import get_tmdb_service, TMDBService
from ..utils import movie_to_response

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


@router.get("/discover", response_model=TMDBSearchResponse)
async def discover_movies(
    tab: Literal["popular", "highly-rated"] = Query(..., description="Tab: 'popular' or 'highly-rated'"),
    page: int = Query(1, ge=1),
    tmdb: TMDBService = Depends(get_tmdb_service)
):
    """Discover movies available for home viewing (streaming/VOD/disc)"""
    # Calculate date range (last 90 days)
    today = datetime.now()
    ninety_days_ago = today - timedelta(days=90)

    release_date_gte = ninety_days_ago.strftime("%Y-%m-%d")
    release_date_lte = today.strftime("%Y-%m-%d")

    if tab == "popular":
        results = await tmdb.discover_movies(
            sort_by="popularity.desc",
            release_date_gte=release_date_gte,
            release_date_lte=release_date_lte,
            with_release_type="4|5",
            page=page
        )
    else:  # highly-rated
        results = await tmdb.discover_movies(
            sort_by="vote_average.desc",
            release_date_gte=release_date_gte,
            release_date_lte=release_date_lte,
            vote_count_gte=50,
            with_release_type="4|5",
            page=page
        )

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

    return movie_to_response(movie)


@router.get("/", response_model=List[MovieResponse])
def get_all_movies(db: Session = Depends(get_db)):
    """Get all movies in the local database"""
    movies = db.query(Movie).all()
    return [movie_to_response(movie) for movie in movies]
