import httpx
import logging
from typing import Optional
from ..config import get_settings

logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"
EMPTY_RESULTS = {"results": [], "page": 1, "total_pages": 0, "total_results": 0}


class TMDBService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.tmdb_api_key
        self.headers = {
            "Authorization": f"Bearer {settings.tmdb_access_token}",
            "Content-Type": "application/json",
        }

    async def _get(self, path: str, *, params: Optional[dict] = None, label: str) -> Optional[dict]:
        """GET an endpoint and return its JSON, or None on 404 / failure."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{TMDB_BASE_URL}{path}",
                    params=params,
                    headers=self.headers,
                )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.error("TMDB %s timeout (params=%s)", label, params)
        except httpx.HTTPStatusError as e:
            logger.error("TMDB %s HTTP error: %s", label, e)
        except httpx.RequestError as e:
            # DNS failures, connection refused, etc.
            logger.error("TMDB %s network error: %s", label, e)
        except ValueError as e:
            # JSON decode error
            logger.error("TMDB %s invalid JSON: %s", label, e)
        return None

    async def search_movies(self, query: str, page: int = 1) -> dict:
        result = await self._get(
            "/search/movie",
            params={"query": query, "page": page, "include_adult": False},
            label="search_movies",
        )
        return result or EMPTY_RESULTS

    async def get_movie(self, tmdb_id: int) -> Optional[dict]:
        return await self._get(
            f"/movie/{tmdb_id}",
            params={"append_to_response": "release_dates,credits,videos"},
            label="get_movie",
        )

    async def get_trending(self, time_window: str = "week", page: int = 1) -> dict:
        result = await self._get(
            f"/trending/movie/{time_window}",
            params={"page": page},
            label="get_trending",
        )
        return result or EMPTY_RESULTS

    async def discover_movies(
        self,
        sort_by: str = "popularity.desc",
        release_date_gte: Optional[str] = None,
        release_date_lte: Optional[str] = None,
        vote_count_gte: Optional[int] = None,
        with_release_type: Optional[str] = "4|5",
        region: str = "US",
        page: int = 1,
    ) -> dict:
        """Discover movies with flexible filters. Pass ``with_release_type=None``
        to skip the home-availability constraint (e.g. for all-time greats)."""
        params: dict = {
            "page": page,
            "sort_by": sort_by,
            "region": region,
            "include_adult": False,
        }
        if with_release_type:
            params["with_release_type"] = with_release_type
        # release_date (not primary_release_date) lets us filter by digital/physical
        # availability when combined with with_release_type.
        if release_date_gte:
            params["release_date.gte"] = release_date_gte
        if release_date_lte:
            params["release_date.lte"] = release_date_lte
        if vote_count_gte:
            params["vote_count.gte"] = vote_count_gte

        result = await self._get("/discover/movie", params=params, label="discover_movies")
        return result or EMPTY_RESULTS

    @staticmethod
    def get_trailer_url(tmdb_data: dict) -> Optional[str]:
        """Extract a YouTube trailer URL from a TMDB movie payload."""
        videos = tmdb_data.get("videos", {}).get("results", [])
        for video_type in ("Trailer", "Teaser"):
            # Prefer official, then any matching type.
            for require_official in (True, False):
                for video in videos:
                    if (
                        video.get("site") == "YouTube"
                        and video.get("type") == video_type
                        and (not require_official or video.get("official", False))
                    ):
                        return f"https://www.youtube.com/watch?v={video['key']}"
        return None

    @staticmethod
    def get_poster_url(poster_path: Optional[str], size: str = "w500") -> Optional[str]:
        if not poster_path:
            return None
        return f"{TMDB_IMAGE_BASE}/{size}{poster_path}"

    @staticmethod
    def get_backdrop_url(backdrop_path: Optional[str], size: str = "w1280") -> Optional[str]:
        if not backdrop_path:
            return None
        return f"{TMDB_IMAGE_BASE}/{size}{backdrop_path}"


def get_tmdb_service() -> TMDBService:
    return TMDBService()
