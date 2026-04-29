import httpx
import structlog
from pydantic import BaseModel
from app.config import get_settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from cachetools import TTLCache

settings = get_settings()
logger = structlog.get_logger()

# Cache weather responses for 10 minutes per city
weather_cache = TTLCache(maxsize=100, ttl=600)

class LiveConditionsInput(BaseModel):
    destination: str
    country_code: str

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(httpx.HTTPError)
)
async def fetch_weather(city: str, country_code: str) -> dict:
    # Check cache first
    cache_key = f"{city}:{country_code}".lower()
    if cache_key in weather_cache:
        logger.info("weather_cache_hit", city=city)
        return weather_cache[cache_key]

    url = f"https://wttr.in/{city}?format=j1"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        if response.status_code != 200:
            return {"error": "Weather fetch failed"}
        data = response.json()
        current = data["current_condition"][0]
        result = {
            "temp_c": current["temp_C"],
            "feels_like_c": current["FeelsLikeC"],
            "description": current["weatherDesc"][0]["value"],
            "humidity": current["humidity"]
        }

    # Store in cache
    weather_cache[cache_key] = result
    logger.info("weather_cache_miss", city=city)
    return result


async def live_conditions_tool(input: LiveConditionsInput) -> dict:
    try:
        weather = await fetch_weather(input.destination, input.country_code)
        return {
            "destination": input.destination,
            "weather": weather,
        }
    except Exception as e:
        return {
            "destination": input.destination,
            "error": str(e),
            "weather": None,
        }