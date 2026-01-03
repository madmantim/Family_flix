import httpx
import logging
from typing import Optional
from ..config import get_settings

logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"


class TMDBService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.tmdb_api_key
        self.headers = {
            "Authorization": f"Bearer {settings.tmdb_access_token}",
            "Content-Type": "application/json"
        }

    async def search_movies(self, query: str, page: int = 1) -> dict:
        """Search for movies by title"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{TMDB_BASE_URL}/search/movie",
                    params={"query": query, "page": page, "include_adult": False},
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error("TMDB search_movies timeout for query: %s", query)
            return {"results": [], "page": 1, "total_pages": 0, "total_results": 0}
        except httpx.HTTPStatusError as e:
            logger.error("TMDB search_movies HTTP error: %s", e)
            return {"results": [], "page": 1, "total_pages": 0, "total_results": 0}

    async def get_movie(self, tmdb_id: int) -> Optional[dict]:
        """Get full movie details"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{TMDB_BASE_URL}/movie/{tmdb_id}",
                    params={"append_to_response": "release_dates,credits,videos"},
                    headers=self.headers
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error("TMDB get_movie timeout for tmdb_id: %d", tmdb_id)
            return None
        except httpx.HTTPStatusError as e:
            logger.error("TMDB get_movie HTTP error for tmdb_id %d: %s", tmdb_id, e)
            return None

    @staticmethod
    def get_trailer_url(tmdb_data: dict) -> Optional[str]:
        """Extract YouTube trailer URL from TMDB movie data"""
        videos = tmdb_data.get("videos", {}).get("results", [])

        # Prefer official trailers, then any trailer, then teasers
        for video_type in ["Trailer", "Teaser"]:
            # First try official videos
            for video in videos:
                if (video.get("site") == "YouTube" and
                    video.get("type") == video_type and
                    video.get("official", False)):
                    return f"https://www.youtube.com/watch?v={video['key']}"
            # Then try non-official
            for video in videos:
                if (video.get("site") == "YouTube" and
                    video.get("type") == video_type):
                    return f"https://www.youtube.com/watch?v={video['key']}"

        return None

    async def get_trending(self, time_window: str = "week", page: int = 1) -> dict:
        """Get trending movies"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{TMDB_BASE_URL}/trending/movie/{time_window}",
                    params={"page": page},
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error("TMDB get_trending timeout for time_window: %s", time_window)
            return {"results": [], "page": 1, "total_pages": 0, "total_results": 0}
        except httpx.HTTPStatusError as e:
            logger.error("TMDB get_trending HTTP error: %s", e)
            return {"results": [], "page": 1, "total_pages": 0, "total_results": 0}

    async def get_popular(self, page: int = 1) -> dict:
        """Get popular movies"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{TMDB_BASE_URL}/movie/popular",
                    params={"page": page},
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error("TMDB get_popular timeout")
            return {"results": [], "page": 1, "total_pages": 0, "total_results": 0}
        except httpx.HTTPStatusError as e:
            logger.error("TMDB get_popular HTTP error: %s", e)
            return {"results": [], "page": 1, "total_pages": 0, "total_results": 0}

    async def discover_movies(
        self,
        sort_by: str = "popularity.desc",
        release_date_gte: str = None,
        release_date_lte: str = None,
        vote_count_gte: int = None,
        with_release_type: str = "4|5",
        region: str = "US",
        page: int = 1
    ) -> dict:
        """Discover movies with flexible filters for home availability"""
        params = {
            "page": page,
            "sort_by": sort_by,
            "with_release_type": with_release_type,
            "region": region,
            "include_adult": False,
        }
        # Use release_date (not primary_release_date) to filter by digital/physical
        # release date when combined with with_release_type
        if release_date_gte:
            params["release_date.gte"] = release_date_gte
        if release_date_lte:
            params["release_date.lte"] = release_date_lte
        if vote_count_gte:
            params["vote_count.gte"] = vote_count_gte

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{TMDB_BASE_URL}/discover/movie",
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error("TMDB discover_movies timeout")
            return {"results": [], "page": 1, "total_pages": 0, "total_results": 0}
        except httpx.HTTPStatusError as e:
            logger.error("TMDB discover_movies HTTP error: %s", e)
            return {"results": [], "page": 1, "total_pages": 0, "total_results": 0}

    @staticmethod
    def get_poster_url(poster_path: str, size: str = "w500") -> Optional[str]:
        """Get full URL for poster image"""
        if not poster_path:
            return None
        return f"{TMDB_IMAGE_BASE}/{size}{poster_path}"

    @staticmethod
    def get_backdrop_url(backdrop_path: str, size: str = "w1280") -> Optional[str]:
        """Get full URL for backdrop image"""
        if not backdrop_path:
            return None
        return f"{TMDB_IMAGE_BASE}/{size}{backdrop_path}"


def get_tmdb_service() -> TMDBService:
    return TMDBService()
