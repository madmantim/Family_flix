from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base


class ContentRating(enum.Enum):
    """Content rating levels for filtering"""
    ALL_AGES = "all_ages"
    TEEN = "teen"  # 13+
    MATURE = "mature"  # 16+
    ADULT = "adult"  # 18+


class SwipeDirection(enum.Enum):
    """Swipe vote direction"""
    YES = "yes"
    NO = "no"


class Member(Base):
    """Family member"""
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    avatar_url = Column(String(500), nullable=True)
    content_filter = Column(SQLEnum(ContentRating), default=ContentRating.ADULT)
    created_at = Column(DateTime, default=datetime.utcnow)

    swipes = relationship("Swipe", back_populates="member")
    watchlist_additions = relationship("WatchlistEntry", back_populates="added_by")


class Movie(Base):
    """Movie from TMDB - cached metadata"""
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    year = Column(Integer, nullable=True)
    overview = Column(String(2000), nullable=True)
    poster_path = Column(String(200), nullable=True)
    backdrop_path = Column(String(200), nullable=True)
    vote_average = Column(Integer, nullable=True)  # Stored as int (0-100)
    content_rating = Column(SQLEnum(ContentRating), default=ContentRating.ALL_AGES)
    runtime = Column(Integer, nullable=True)  # Minutes
    genres = Column(String(500), nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    swipes = relationship("Swipe", back_populates="movie")
    watchlist_entries = relationship("WatchlistEntry", back_populates="movie")
    watch_history = relationship("WatchHistory", back_populates="movie")


class WatchlistEntry(Base):
    """Movie added to the shared pool"""
    __tablename__ = "watchlist_entries"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    added_by_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    source = Column(String(50), default="manual")  # manual, curated, trending
    added_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # False when watched

    movie = relationship("Movie", back_populates="watchlist_entries")
    added_by = relationship("Member", back_populates="watchlist_additions")


class Swipe(Base):
    """Individual vote on a movie"""
    __tablename__ = "swipes"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    direction = Column(SQLEnum(SwipeDirection), nullable=False)
    swiped_at = Column(DateTime, default=datetime.utcnow)

    member = relationship("Member", back_populates="swipes")
    movie = relationship("Movie", back_populates="swipes")

    class Config:
        # Unique constraint: one swipe per member per movie
        __table_args__ = (
            {"sqlite_autoincrement": True},
        )


class WatchHistory(Base):
    """Movies that have been watched"""
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    watched_at = Column(DateTime, default=datetime.utcnow)
    watchers = Column(String(500), nullable=True)  # JSON array of member IDs

    movie = relationship("Movie", back_populates="watch_history")
