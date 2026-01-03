from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from ..database import get_db
from ..models import Movie, WatchlistEntry, Member, ContentRating
from ..schemas import WatchlistEntryCreate, WatchlistEntryResponse, MovieResponse
from ..services.tmdb import get_tmdb_service, TMDBService
from ..services.omdb import get_omdb_service, OMDbService

router = APIRouter()


@router.get("/", response_model=List[WatchlistEntryResponse])
def get_watchlist(
    active_only: bool = True,
    added_by_id: int = None,
    db: Session = Depends(get_db)
):
    """Get all movies in the pool"""
    query = db.query(WatchlistEntry)

    if active_only:
        query = query.filter(WatchlistEntry.is_active == True)

    if added_by_id:
        query = query.filter(WatchlistEntry.added_by_id == added_by_id)

    entries = query.order_by(WatchlistEntry.added_at.desc()).all()

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
            "added_by": entry.added_by,
            "source": entry.source,
            "added_at": entry.added_at,
            "is_active": entry.is_active
        })

    return result


@router.post("/", response_model=WatchlistEntryResponse, status_code=201)
async def add_to_watchlist(
    entry: WatchlistEntryCreate,
    db: Session = Depends(get_db),
    tmdb: TMDBService = Depends(get_tmdb_service),
    omdb: OMDbService = Depends(get_omdb_service)
):
    """Add a movie to the pool by TMDB ID"""
    # Validate member exists
    member = db.query(Member).filter(Member.id == entry.added_by_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Check if movie already in DB
    movie = db.query(Movie).filter(Movie.tmdb_id == entry.tmdb_id).first()

    if not movie:
        # Fetch from TMDB and create
        tmdb_data = await tmdb.get_movie(entry.tmdb_id)
        if not tmdb_data:
            raise HTTPException(status_code=404, detail="Movie not found on TMDB")

        # Parse release date for year
        year = None
        if tmdb_data.get("release_date"):
            try:
                year = int(tmdb_data["release_date"][:4])
            except (ValueError, IndexError):
                pass

        # Determine content rating from release_dates
        content_rating = ContentRating.ALL_AGES
        release_dates = tmdb_data.get("release_dates", {}).get("results", [])
        found_rating = False
        for country in release_dates:
            if found_rating:
                break
            if country.get("iso_3166_1") in ["AU", "US"]:
                for release in country.get("release_dates", []):
                    cert = release.get("certification", "").strip()
                    if not cert:
                        continue  # Skip empty certifications
                    if cert in ["R18+", "NC-17", "X"]:
                        content_rating = ContentRating.ADULT
                        found_rating = True
                        break
                    elif cert in ["MA15+", "MA 15+", "R", "MA"]:
                        content_rating = ContentRating.MATURE
                        found_rating = True
                        break
                    elif cert in ["M", "PG-13", "PG"]:
                        content_rating = ContentRating.TEEN
                        found_rating = True
                        break

        # Extract genres
        genres = json.dumps([g["name"] for g in tmdb_data.get("genres", [])])

        # Get IMDB ID from TMDB response
        imdb_id = tmdb_data.get("imdb_id")

        # Fetch Rotten Tomatoes scores from OMDb
        rt_critic_score = None
        rt_audience_score = None
        rt_url = None
        if imdb_id:
            omdb_data = await omdb.get_ratings_by_imdb_id(imdb_id)
            if omdb_data:
                rt_critic_score = omdb_data.get("rt_critic_score")
                rt_audience_score = omdb_data.get("rt_audience_score")
                rt_url = omdb_data.get("rt_url")

        # Extract trailer URL from TMDB videos
        trailer_url = TMDBService.get_trailer_url(tmdb_data)

        movie = Movie(
            tmdb_id=entry.tmdb_id,
            title=tmdb_data["title"],
            year=year,
            overview=tmdb_data.get("overview"),
            poster_path=tmdb_data.get("poster_path"),
            backdrop_path=tmdb_data.get("backdrop_path"),
            vote_average=int(tmdb_data.get("vote_average", 0) * 10),
            content_rating=content_rating,
            runtime=tmdb_data.get("runtime"),
            genres=genres,
            imdb_id=imdb_id,
            rt_critic_score=rt_critic_score,
            rt_audience_score=rt_audience_score,
            rt_url=rt_url,
            trailer_url=trailer_url
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)

    # Check if already in active watchlist
    existing = db.query(WatchlistEntry).filter(
        WatchlistEntry.movie_id == movie.id,
        WatchlistEntry.is_active == True
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Movie already in watchlist")

    # Create watchlist entry
    watchlist_entry = WatchlistEntry(
        movie_id=movie.id,
        added_by_id=entry.added_by_id,
        source=entry.source
    )
    db.add(watchlist_entry)
    db.commit()
    db.refresh(watchlist_entry)

    return {
        "id": watchlist_entry.id,
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
        "added_by": member,
        "source": watchlist_entry.source,
        "added_at": watchlist_entry.added_at,
        "is_active": watchlist_entry.is_active
    }


@router.delete("/{entry_id}", status_code=204)
def remove_from_watchlist(entry_id: int, db: Session = Depends(get_db)):
    """Remove a movie from the pool"""
    entry = db.query(WatchlistEntry).filter(WatchlistEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")

    entry.is_active = False
    db.commit()
