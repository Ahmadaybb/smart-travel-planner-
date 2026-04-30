import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.state import ml_model, embedder


@pytest.fixture(autouse=True)
def load_models():
    import joblib
    from sentence_transformers import SentenceTransformer
    from app.config import get_settings
    settings = get_settings()
    ml_model["classifier"] = joblib.load(settings.ML_MODEL_PATH)
    embedder["model"] = SentenceTransformer("all-MiniLM-L6-v2")


@pytest.mark.asyncio
async def test_agent_runs_all_three_tools():
    from app.db import AsyncSessionLocal
    from app.agent.agent import run_agent

    # Mock cheap LLM to return tool calls
    mock_cheap = MagicMock()
    mock_cheap.ainvoke = AsyncMock(return_value=MagicMock(
        tool_calls=[
            {
                "id": "1",
                "name": "rag_tool",
                "args": {"query": "hiking July $1500", "top_k": 3}
            },
            {
                "id": "2",
                "name": "classifier_tool",
                "args": {
                    "avg_cost_per_day_usd": 100,
                    "avg_temp_july_celsius": 20,
                    "hiking_score": 5,
                    "beach_score": 1,
                    "museums_count": 2,
                    "unesco_sites": 1,
                    "tourist_density": 3,
                    "family_friendly_score": 3,
                    "safety_score": 4,
                    "avg_meal_cost_usd": 15
                }
            },
            {
                "id": "3",
                "name": "live_conditions_tool",
                "args": {"destination": "Banff", "country_code": "CA"}
            }
        ],
        usage_metadata={"total_tokens": 100}
    ))

    # Mock strong LLM to return final answer
    mock_strong = MagicMock()
    mock_strong.ainvoke = AsyncMock(return_value=MagicMock(
        content="Your trip plan to Banff is ready!",
        usage_metadata={"total_tokens": 200}
    ))

    with patch("app.agent.agent.cheap_llm", mock_cheap), \
         patch("app.agent.agent.strong_llm", mock_strong):

        async with AsyncSessionLocal() as db:
            result = await run_agent(
                "I have 2 weeks in July and $1500. I like hiking.",
                db
            )

    assert "answer" in result
    assert "tool_calls" in result
    assert len(result["tool_calls"]) == 3
    assert result["answer"] == "Your trip plan to Banff is ready!"


@pytest.mark.asyncio
async def test_agent_blocks_unknown_tool():
    from app.agent.agent import run_tool
    from app.db import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await run_tool("evil_tool", {}, db)

    import json
    parsed = json.loads(result)
    assert "error" in parsed
    assert "not allowed" in parsed["error"]


@pytest.mark.asyncio
async def test_agent_handles_tool_error_gracefully():
    from app.agent.agent import run_tool
    from app.db import AsyncSessionLocal

    # Pass invalid args to classifier — should return error not crash
    async with AsyncSessionLocal() as db:
        result = await run_tool(
            "classifier_tool",
            {"invalid_field": "bad_data"},
            db
        )

    import json
    parsed = json.loads(result)
    assert "error" in parsed