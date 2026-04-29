import httpx
import logging
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
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
    payload = {
        "user": user_email,
        "query": query,
        "answer": answer,
        "tools_used": [t["tool_name"] for t in tool_calls]
    }

    try:
        await _send_webhook(payload)
        logger.info("webhook_delivered", user=user_email)

    except Exception as e:
        # Log failure but never raise — webhook must not break user response
        logger.error(
            "webhook_failed",
            user=user_email,
            error=str(e)
        )