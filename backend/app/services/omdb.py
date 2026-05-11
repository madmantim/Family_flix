import httpx
import logging
from typing import Optional
from ..config import get_settings

logger = logging.getLogger(__name__)

OMDB_BASE_URL = "https://www.omdbapi.com"


class OMDbService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.omdb_api_key

    async def _fetch(self, params: dict, *, label: str) -> Optional[dict]:
        """GET OMDb and return the parsed payload, or None on any failure."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(OMDB_BASE_URL, params=params)
            if response.status_code != 200:
                return None
            data = response.json()
            if data.get("Response") == "False":
                return None
            return data
        except httpx.TimeoutException:
            logger.error("OMDb %s timeout (params=%s)", label, params)
        except httpx.RequestError as e:
            logger.error("OMDb %s network error: %s", label, e)
        except ValueError as e:
            logger.error("OMDb %s invalid JSON: %s", label, e)
        return None

    async def get_ratings_by_imdb_id(self, imdb_id: str) -> Optional[dict]:
        """Get movie ratings from OMDb using IMDB ID."""
        if not self.api_key or not imdb_id:
            return None

        data = await self._fetch(
            {"i": imdb_id, "apikey": self.api_key},
            label="by_imdb_id",
        )
        if data is None:
            return None

        return {
            "rt_critic_score": _extract_rt_score(data),
            "rt_audience_score": None,  # OMDb doesn't reliably provide this
            # Don't synthesise the RT URL — slug guessing is wrong often enough
            # that storing a broken link is worse than no link.
            "rt_url": None,
            "imdb_rating": data.get("imdbRating"),
            "metascore": data.get("Metascore"),
        }

    async def get_ratings_by_title(self, title: str, year: Optional[int] = None) -> Optional[dict]:
        """Get movie ratings from OMDb by title search."""
        if not self.api_key:
            return None

        params = {"t": title, "apikey": self.api_key, "type": "movie"}
        if year:
            params["y"] = str(year)

        data = await self._fetch(params, label="by_title")
        if data is None:
            return None

        return {
            "rt_critic_score": _extract_rt_score(data),
            "rt_audience_score": None,
            "rt_url": None,
            "imdb_id": data.get("imdbID"),
            "imdb_rating": data.get("imdbRating"),
            "metascore": data.get("Metascore"),
        }


def _extract_rt_score(data: dict) -> Optional[int]:
    for rating in data.get("Ratings", []) or []:
        if rating.get("Source") == "Rotten Tomatoes":
            try:
                return int(str(rating.get("Value", "")).replace("%", ""))
            except (ValueError, AttributeError):
                return None
    return None


def get_omdb_service() -> OMDbService:
    return OMDbService()
