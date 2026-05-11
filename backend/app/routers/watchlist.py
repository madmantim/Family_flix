from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import json
from ..database import get_db
from ..models import Movie, WatchlistEntry, Member, ContentRating, Swipe, SwipeDirection, MemberWatched
from ..schemas import (
    WatchlistEntryCreate,
    WatchlistEntryResponse,
    MovieResponse,
    BulkWatchlistUpdateRequest,
    BulkWatchlistUpdateResponse,
)
from ..services.tmdb import get_tmdb_service, TMDBService
from ..services.omdb import get_omdb_service, OMDbService
from ..utils import movie_to_response

router = APIRouter()

# AU certs are checked before US so Australian ratings (the family's locale) win
# when both regions ship a certification for the same release.
RATING_BY_CERT = {
    "R18+": ContentRating.ADULT, "NC-17": ContentRating.ADULT, "X": ContentRating.ADULT,
    "MA15+": ContentRating.MATURE, "MA 15+": ContentRating.MATURE,
    "R": ContentRating.MATURE, "MA": ContentRating.MATURE,
    "M": ContentRating.TEEN, "PG-13": ContentRating.TEEN, "PG": ContentRating.TEEN,
    # AU all-ages certs ("G" general, "E" exempt) and US "G". Without these, an
    # AU-rated G film would fall through to a stricter US cert.
    "G": ContentRating.ALL_AGES, "E": ContentRating.ALL_AGES,
}
PREFERRED_REGIONS = ("AU", "US")


def derive_content_rating(release_dates_payload: dict) -> ContentRating:
    """Map TMDB release_dates payload to our ContentRating, preferring AU certs over US."""
    results = release_dates_payload.get("results", []) or []
    by_region = {entry.get("iso_3166_1"): entry for entry in results}
    for region in PREFERRED_REGIONS:
        entry = by_region.get(region)
        if not entry:
            continue
        for release in entry.get("release_dates", []) or []:
            cert = (release.get("certification") or "").strip()
            if cert in RATING_BY_CERT:
                return RATING_BY_CERT[cert]
    return ContentRating.ALL_AGES


@router.get("/", response_model=List[WatchlistEntryResponse])
def get_watchlist(
    active_only: bool = True,
    added_by_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all movies in the pool"""
    query = db.query(WatchlistEntry).options(
        joinedload(WatchlistEntry.movie),
        joinedload(WatchlistEntry.added_by)
    )

    if active_only:
        query = query.filter(WatchlistEntry.is_active == True)

    if added_by_id:
        query = query.filter(WatchlistEntry.added_by_id == added_by_id)

    entries = query.order_by(WatchlistEntry.added_at.desc()).all()

    result = []
    for entry in entries:
        result.append({
            "id": entry.id,
            "movie": movie_to_response(entry.movie),
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

    # Check if movie already in DB. We may race with another request creating
    # the same movie; handled below by catching IntegrityError on flush().
    movie = db.query(Movie).filter(Movie.tmdb_id == entry.tmdb_id).first()

    if not movie:
        tmdb_data = await tmdb.get_movie(entry.tmdb_id)
        if not tmdb_data:
            raise HTTPException(status_code=404, detail="Movie not found on TMDB")

        year = None
        if tmdb_data.get("release_date"):
            try:
                year = int(tmdb_data["release_date"][:4])
            except (ValueError, IndexError):
                pass

        content_rating = derive_content_rating(tmdb_data.get("release_dates", {}) or {})
        genres = json.dumps([g["name"] for g in tmdb_data.get("genres", [])])
        imdb_id = tmdb_data.get("imdb_id")

        rt_critic_score = None
        rt_audience_score = None
        rt_url = None
        if imdb_id:
            omdb_data = await omdb.get_ratings_by_imdb_id(imdb_id)
            if omdb_data:
                rt_critic_score = omdb_data.get("rt_critic_score")
                rt_audience_score = omdb_data.get("rt_audience_score")
                rt_url = omdb_data.get("rt_url")

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
            trailer_url=trailer_url,
        )
        db.add(movie)
        try:
            db.flush()  # Get movie.id without committing yet
        except IntegrityError:
            # Concurrent insert won the race on the tmdb_id unique constraint.
            # Recover by loading the row the other request created.
            db.rollback()
            movie = db.query(Movie).filter(Movie.tmdb_id == entry.tmdb_id).first()
            if not movie:
                raise HTTPException(status_code=500, detail="Failed to add movie")

    # Check if already in active watchlist (within the same transaction)
    existing = db.query(WatchlistEntry).filter(
        WatchlistEntry.movie_id == movie.id,
        WatchlistEntry.is_active == True,
    ).first()
    if existing:
        db.rollback()
        raise HTTPException(status_code=400, detail="Movie already in watchlist")

    watchlist_entry = WatchlistEntry(
        movie_id=movie.id,
        added_by_id=entry.added_by_id,
        source=entry.source,
    )
    db.add(watchlist_entry)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Movie already in watchlist")
    db.refresh(watchlist_entry)

    return {
        "id": watchlist_entry.id,
        "movie": movie_to_response(movie),
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


@router.post("/bulk-update", response_model=BulkWatchlistUpdateResponse)
def bulk_update_watchlist(
    request: BulkWatchlistUpdateRequest,
    db: Session = Depends(get_db),
):
    """Bulk apply a personal watchlist action to several movies.

    Both actions flip the member's swipe to NO (so the films drop off their
    liked grid). `mark_watched=True` additionally records a MemberWatched row
    for the member. The shared pool is not touched — other members are
    unaffected. Idempotent.
    """
    member = db.query(Member).filter(Member.id == request.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    valid_movie_ids = {
        mid for (mid,) in db.query(Movie.id).filter(Movie.id.in_(request.movie_ids)).all()
    }
    missing = set(request.movie_ids) - valid_movie_ids
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Movies not found: {sorted(missing)}",
        )

    # Two concurrent bulk requests can both observe "no existing watched row"
    # and both try to INSERT — the loser hits the unique constraint. Retry
    # once after re-reading state; the second pass is deterministic.
    watched_recorded = 0
    for attempt in (1, 2):
        try:
            watched_recorded = _apply_bulk_updates(
                db,
                member_id=request.member_id,
                movie_ids=valid_movie_ids,
                mark_watched=request.mark_watched,
            )
            db.commit()
            break
        except IntegrityError:
            db.rollback()
            if attempt == 2:
                # A persistent integrity failure on retry is genuinely unexpected.
                raise HTTPException(status_code=500, detail="Bulk update failed")

    return BulkWatchlistUpdateResponse(
        updated_count=len(valid_movie_ids),
        watched_recorded=watched_recorded,
    )


def _apply_bulk_updates(db, *, member_id, movie_ids, mark_watched) -> int:
    """Apply the bulk update in the current session (no commit). Returns the
    number of new MemberWatched rows created."""
    existing_swipes = {
        s.movie_id: s
        for s in db.query(Swipe).filter(
            Swipe.member_id == member_id,
            Swipe.movie_id.in_(movie_ids),
        ).all()
    }
    existing_watched: set[int] = set()
    if mark_watched:
        existing_watched = {
            mw.movie_id
            for mw in db.query(MemberWatched).filter(
                MemberWatched.member_id == member_id,
                MemberWatched.movie_id.in_(movie_ids),
            ).all()
        }

    watched_recorded = 0
    for movie_id in movie_ids:
        existing = existing_swipes.get(movie_id)
        if existing:
            existing.direction = SwipeDirection.NO
        else:
            db.add(Swipe(
                member_id=member_id,
                movie_id=movie_id,
                direction=SwipeDirection.NO,
            ))

        if mark_watched and movie_id not in existing_watched:
            db.add(MemberWatched(
                member_id=member_id,
                movie_id=movie_id,
            ))
            watched_recorded += 1

    return watched_recorded
