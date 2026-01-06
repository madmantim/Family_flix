from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from .models import ContentRating, SwipeDirection


# Member schemas
class MemberBase(BaseModel):
    name: str = Field(..., max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    content_filter: ContentRating = ContentRating.ADULT


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    content_filter: Optional[ContentRating] = None


class MemberResponse(MemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# Movie schemas
class MovieBase(BaseModel):
    tmdb_id: int
    title: str = Field(..., max_length=500)
    year: Optional[int] = None
    overview: Optional[str] = Field(None, max_length=2000)
    poster_path: Optional[str] = Field(None, max_length=200)
    backdrop_path: Optional[str] = Field(None, max_length=200)
    vote_average: Optional[int] = None
    content_rating: ContentRating = ContentRating.ALL_AGES
    runtime: Optional[int] = None
    genres: Optional[str] = Field(None, max_length=500)
    imdb_id: Optional[str] = Field(None, max_length=20)
    rt_critic_score: Optional[int] = None
    rt_audience_score: Optional[int] = None
    rt_url: Optional[str] = Field(None, max_length=500)
    trailer_url: Optional[str] = Field(None, max_length=500)


class MovieCreate(MovieBase):
    pass


class MovieResponse(MovieBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    created_at: datetime


# Swipe schemas
class SwipeCreate(BaseModel):
    member_id: int
    movie_id: int
    direction: SwipeDirection
    watched: bool = False  # If true, creates MemberWatched record


class SwipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    movie_id: int
    direction: SwipeDirection
    swiped_at: datetime


# Watchlist schemas
class WatchlistEntryCreate(BaseModel):
    tmdb_id: int
    added_by_id: int
    source: str = Field("manual", max_length=50)


class WatchlistEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie: MovieResponse
    added_by: MemberResponse
    source: str
    added_at: datetime
    is_active: bool


# Movie Night schemas
class MovieNightRequest(BaseModel):
    present_member_ids: List[int]


class MatchedMovie(BaseModel):
    movie: MovieResponse
    yes_votes: int
    total_present: int
    is_full_match: bool
    voters: List[MemberResponse]
    absent_yes_voters: List[MemberResponse] = []


class MovieNightResponse(BaseModel):
    matches: List[MatchedMovie]
    present_members: List[MemberResponse]


# Swipe queue
class SwipeQueueResponse(BaseModel):
    movies: List[MovieResponse]
    total_unswiped: int


# TMDB search results
class TMDBSearchResult(BaseModel):
    tmdb_id: int
    title: str
    year: Optional[int] = None
    overview: Optional[str] = None
    poster_url: Optional[str] = None
    vote_average: Optional[float] = None


class TMDBSearchResponse(BaseModel):
    results: List[TMDBSearchResult]
    page: int
    total_pages: int
    total_results: int


# Member Watched schemas
class MemberWatchedCreate(BaseModel):
    member_id: int
    movie_id: int


class MemberWatchedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    movie_id: int
    watched_at: datetime


class MemberWatchedWithMovie(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie: MovieResponse
    watched_at: datetime


class MarkWatchedRequest(BaseModel):
    movie_id: int
    member_ids: List[int]
