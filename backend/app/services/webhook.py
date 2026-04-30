import httpx
import json
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_groq import ChatGroq
from app.config import get_settings

settings = get_settings()
logger = structlog.get_logger()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(httpx.HTTPError)
)
async def _send_webhook(payload: dict) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            settings.WEBHOOK_URL,
            json=payload
        )
        response.raise_for_status()



async def deliver_webhook(
    user_email: str,
    query: str,
    answer: str,
    tool_calls: list[dict]
) -> None:
    try:
        payload = {
            "user_email": user_email,
            "answer": answer
        }

        await _send_webhook(payload)
        logger.info("webhook_delivered", user=user_email)

    except Exception as e:
        logger.error("webhook_failed", user=user_email, error=str(e))