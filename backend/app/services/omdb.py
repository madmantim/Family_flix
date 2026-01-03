import httpx
import logging
from typing import Optional
from ..config import get_settings

logger = logging.getLogger(__name__)

OMDB_BASE_URL = "http://www.omdbapi.com"


class OMDbService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.omdb_api_key

    async def get_ratings_by_imdb_id(self, imdb_id: str) -> Optional[dict]:
        """Get movie ratings from OMDb using IMDB ID"""
        if not self.api_key or not imdb_id:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    OMDB_BASE_URL,
                    params={"i": imdb_id, "apikey": self.api_key}
                )
                if response.status_code != 200:
                    return None

                data = response.json()
                if data.get("Response") == "False":
                    return None

                # Extract RT scores from Ratings array
                rt_critic = None
                rt_audience = None

                for rating in data.get("Ratings", []):
                    source = rating.get("Source", "")
                    value = rating.get("Value", "")

                    if source == "Rotten Tomatoes":
                        # Format: "91%"
                        try:
                            rt_critic = int(value.replace("%", ""))
                        except (ValueError, AttributeError):
                            pass

                # OMDb doesn't always have audience score in Ratings
                # But we can construct the RT URL from the title
                title = data.get("Title", "")
                year = data.get("Year", "")

                # Construct RT URL (best effort - may not always be exact)
                rt_url = None
                if title:
                    # RT URL format: https://www.rottentomatoes.com/m/movie_name
                    slug = title.lower()
                    slug = slug.replace(":", "")
                    slug = slug.replace("'", "")
                    slug = slug.replace("&", "and")
                    slug = slug.replace(" - ", "_")
                    slug = slug.replace(" ", "_")
                    slug = "".join(c for c in slug if c.isalnum() or c == "_")
                    rt_url = f"https://www.rottentomatoes.com/m/{slug}"

                return {
                    "rt_critic_score": rt_critic,
                    "rt_audience_score": rt_audience,  # OMDb doesn't reliably provide this
                    "rt_url": rt_url,
                    "imdb_rating": data.get("imdbRating"),
                    "metascore": data.get("Metascore"),
                }
        except httpx.TimeoutException:
            logger.error("OMDb get_ratings_by_imdb_id timeout for imdb_id: %s", imdb_id)
            return None
        except httpx.HTTPStatusError as e:
            logger.error("OMDb get_ratings_by_imdb_id HTTP error for imdb_id %s: %s", imdb_id, e)
            return None

    async def get_ratings_by_title(self, title: str, year: Optional[int] = None) -> Optional[dict]:
        """Get movie ratings from OMDb by title search"""
        if not self.api_key:
            return None

        params = {"t": title, "apikey": self.api_key, "type": "movie"}
        if year:
            params["y"] = str(year)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(OMDB_BASE_URL, params=params)
                if response.status_code != 200:
                    return None

                data = response.json()
                if data.get("Response") == "False":
                    return None

                # Same extraction as above
                rt_critic = None
                for rating in data.get("Ratings", []):
                    if rating.get("Source") == "Rotten Tomatoes":
                        try:
                            rt_critic = int(rating.get("Value", "").replace("%", ""))
                        except (ValueError, AttributeError):
                            pass

                title = data.get("Title", "")
                slug = title.lower()
                slug = slug.replace(":", "")
                slug = slug.replace("'", "")
                slug = slug.replace("&", "and")
                slug = slug.replace(" - ", "_")
                slug = slug.replace(" ", "_")
                slug = "".join(c for c in slug if c.isalnum() or c == "_")
                rt_url = f"https://www.rottentomatoes.com/m/{slug}"

                return {
                    "rt_critic_score": rt_critic,
                    "rt_audience_score": None,
                    "rt_url": rt_url,
                    "imdb_id": data.get("imdbID"),
                    "imdb_rating": data.get("imdbRating"),
                    "metascore": data.get("Metascore"),
                }
        except httpx.TimeoutException:
            logger.error("OMDb get_ratings_by_title timeout for title: %s", title)
            return None
        except httpx.HTTPStatusError as e:
            logger.error("OMDb get_ratings_by_title HTTP error for title %s: %s", title, e)
            return None


def get_omdb_service() -> OMDbService:
    return OMDbService()
