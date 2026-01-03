"""Utility functions for the Family Flix Picker app"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Movie


def movie_to_response(movie: "Movie") -> dict:
    """Convert a Movie model to a response dictionary with computed URLs"""
    from .services.tmdb import TMDBService

    return {
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
    }
