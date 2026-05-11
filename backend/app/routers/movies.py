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


def _parse_year(release_date) -> Optional[int]:
    if not release_date or not isinstance(release_date, str):
        return None
    try:
        return int(release_date[:4])
    except (ValueError, TypeError):
        return None


def _to_search_result(tmdb: TMDBService, raw: dict) -> Optional[TMDBSearchResult]:
    tmdb_id = raw.get("id")
    title = raw.get("title")
    if not tmdb_id or not title:
        return None
    return TMDBSearchResult(
        tmdb_id=tmdb_id,
        title=title,
        year=_parse_year(raw.get("release_date")),
        overview=raw.get("overview"),
        poster_url=tmdb.get_poster_url(raw.get("poster_path")),
        vote_average=raw.get("vote_average"),
    )


def _to_search_response(tmdb: TMDBService, results: dict) -> TMDBSearchResponse:
    mapped = (_to_search_result(tmdb, m) for m in results.get("results", []) or [])
    return TMDBSearchResponse(
        results=[r for r in mapped if r is not None],
        page=results.get("page", 1),
        total_pages=results.get("total_pages", 0),
        total_results=results.get("total_results", 0),
    )


@router.get("/search", response_model=TMDBSearchResponse)
async def search_movies(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    tmdb: TMDBService = Depends(get_tmdb_service)
):
    """Search TMDB for movies"""
    results = await tmdb.search_movies(query, page)
    return _to_search_response(tmdb, results)


@router.get("/trending", response_model=TMDBSearchResponse)
async def get_trending(
    page: int = Query(1, ge=1),
    tmdb: TMDBService = Depends(get_tmdb_service)
):
    """Get trending movies from TMDB"""
    results = await tmdb.get_trending("week", page)
    return _to_search_response(tmdb, results)


@router.get("/discover", response_model=TMDBSearchResponse)
async def discover_movies(
    tab: Literal["trending", "popular", "highly-rated", "all-time"] = Query(
        ...,
        description=(
            "trending: TMDB's trending-this-week list (any era); "
            "popular: last 90 days, sorted by popularity; "
            "highly-rated: last 90 days, top-voted; "
            "all-time: any era, top-voted with significant vote count."
        ),
    ),
    page: int = Query(1, ge=1),
    tmdb: TMDBService = Depends(get_tmdb_service),
):
    """Discover movies via TMDB across four tabs."""
    today = datetime.now()
    ninety_days_ago = today - timedelta(days=90)
    recent_window = dict(
        release_date_gte=ninety_days_ago.strftime("%Y-%m-%d"),
        release_date_lte=today.strftime("%Y-%m-%d"),
        with_release_type="4|5",
        page=page,
    )

    if tab == "trending":
        # TMDB's curated trending list — distinct from "popular recent".
        results = await tmdb.get_trending(time_window="week", page=page)
    elif tab == "popular":
        results = await tmdb.discover_movies(sort_by="popularity.desc", **recent_window)
    elif tab == "highly-rated":
        results = await tmdb.discover_movies(
            sort_by="vote_average.desc",
            vote_count_gte=50,
            **recent_window,
        )
    else:  # all-time
        # No date filter; require enough votes to weed out small-sample-size flukes.
        results = await tmdb.discover_movies(
            sort_by="vote_average.desc",
            vote_count_gte=1000,
            with_release_type=None,  # don't restrict by home-release type
            page=page,
        )

    return _to_search_response(tmdb, results)


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
