import httpx
from typing import Optional
from ..config import get_settings

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
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TMDB_BASE_URL}/search/movie",
                params={"query": query, "page": page, "include_adult": False},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_movie(self, tmdb_id: int) -> Optional[dict]:
        """Get full movie details"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TMDB_BASE_URL}/movie/{tmdb_id}",
                params={"append_to_response": "release_dates,credits,videos"},
                headers=self.headers
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

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
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TMDB_BASE_URL}/trending/movie/{time_window}",
                params={"page": page},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_popular(self, page: int = 1) -> dict:
        """Get popular movies"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TMDB_BASE_URL}/movie/popular",
                params={"page": page},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

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
