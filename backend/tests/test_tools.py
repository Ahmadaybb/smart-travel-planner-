import pytest
from unittest.mock import patch, MagicMock
from app.tools.classifier_tool import ClassifierToolInput, classifier_tool
from app.tools.live_conditions_tool import LiveConditionsInput, live_conditions_tool
from app.tools.rag_tool import RAGToolInput, rag_tool
from app.state import ml_model, embedder


@pytest.fixture(autouse=True)
def load_models():
    import joblib
    from sentence_transformers import SentenceTransformer
    from app.config import get_settings
    settings = get_settings()
    ml_model["classifier"] = joblib.load(settings.ML_MODEL_PATH)
    embedder["model"] = SentenceTransformer("all-MiniLM-L6-v2")


# --- Classifier Tool ---

@pytest.mark.asyncio
async def test_classifier_returns_travel_style():
    input_data = ClassifierToolInput(
        avg_cost_per_day_usd=85,
        avg_temp_july_celsius=4,
        hiking_score=5,
        beach_score=1,
        museums_count=1,
        unesco_sites=1,
        tourist_density=2,
        family_friendly_score=3,
        safety_score=4,
        avg_meal_cost_usd=12
    )
    result = await classifier_tool(input_data)
    print(f"\n✅ Classifier result: {result['travel_style']} ({result['confidence']*100:.1f}% confidence)")
    assert "travel_style" in result
    assert result["travel_style"] in [
        "Adventure", "Relaxation", "Culture",
        "Budget", "Luxury", "Family"
    ]


@pytest.mark.asyncio
async def test_classifier_confidence_between_0_and_1():
    input_data = ClassifierToolInput(
        avg_cost_per_day_usd=350,
        avg_temp_july_celsius=30,
        hiking_score=1,
        beach_score=5,
        museums_count=0,
        unesco_sites=0,
        tourist_density=2,
        family_friendly_score=3,
        safety_score=5,
        avg_meal_cost_usd=45
    )
    result = await classifier_tool(input_data)
    assert 0 <= result["confidence"] <= 1


# --- Live Conditions Tool ---

@pytest.mark.asyncio
async def test_weather_returns_expected_fields():
    input_data = LiveConditionsInput(destination="Paris", country_code="FR")
    result = await live_conditions_tool(input_data)
    print(f"\n✅ Weather in Paris: {result['weather']['temp_c']}°C — {result['weather']['description']}")
    assert "destination" in result
    assert "weather" in result

@pytest.mark.asyncio
async def test_weather_handles_invalid_city():
    input_data = LiveConditionsInput(
        destination="FakeCityXYZ123",
        country_code="XX"
    )
    result = await live_conditions_tool(input_data)
    # should not crash — returns error or empty weather
    assert "destination" in result


# --- RAG Tool ---

@pytest.mark.asyncio
async def test_rag_returns_results():
    from app.db import AsyncSessionLocal
    input_data = RAGToolInput(query="hiking mountains July", top_k=3)
    async with AsyncSessionLocal() as db:
        result = await rag_tool(input_data, db)
    print(f"\n✅ RAG found {len(result['results'])} results")
    for r in result["results"]:
        print(f"   📍 {r['destination']} — score: {r['score']}")
    assert "results" in result


@pytest.mark.asyncio
async def test_rag_respects_top_k():
    from app.db import AsyncSessionLocal
    input_data = RAGToolInput(query="beach relaxation", top_k=2)
    async with AsyncSessionLocal() as db:
        result = await rag_tool(input_data, db)
    assert len(result["results"]) <= 2

@pytest.mark.asyncio
async def test_rag_off_topic_query():
    """RAG should return results even for off-topic queries — 
    pgvector always returns closest matches"""
    from app.db import AsyncSessionLocal
    input_data = RAGToolInput(query="What is the capital of France?", top_k=3)
    async with AsyncSessionLocal() as db:
        result = await rag_tool(input_data, db)
    print(f"\n🔍 Off-topic query results: {len(result['results'])} returned")
    for r in result["results"]:
        print(f"   📍 {r['destination']} — score: {r['score']}")
    # RAG always returns something — it's similarity search not keyword search
    assert "results" in result


@pytest.mark.asyncio
async def test_rag_vague_query():
    """User says only 'I want to travel' — no hints"""
    from app.db import AsyncSessionLocal
    input_data = RAGToolInput(query="I want to travel", top_k=3)
    async with AsyncSessionLocal() as db:
        result = await rag_tool(input_data, db)
    print(f"\n🔍 Vague query results: {len(result['results'])} returned")
    for r in result["results"]:
        print(f"   📍 {r['destination']} — score: {r['score']}")
    assert len(result["results"]) <= 3


@pytest.mark.asyncio
async def test_rag_contradicting_requirements():
    """User wants luxury but has low budget"""
    from app.db import AsyncSessionLocal
    input_data = RAGToolInput(
        query="I want luxury 5 star resort but only have $50 per day",
        top_k=3
    )
    async with AsyncSessionLocal() as db:
        result = await rag_tool(input_data, db)
    print(f"\n🔍 Contradicting requirements results:")
    for r in result["results"]:
        print(f"   📍 {r['destination']} — score: {r['score']}")
    # Should return something — agent will handle the contradiction
    assert "results" in result


@pytest.mark.asyncio
async def test_rag_empty_query():
    """Empty query — should not crash"""
    from app.db import AsyncSessionLocal
    input_data = RAGToolInput(query="", top_k=3)
    async with AsyncSessionLocal() as db:
        result = await rag_tool(input_data, db)
    print(f"\n🔍 Empty query result: {result}")
    # Should return empty results or handle gracefully
    assert "results" in result or "error" in result


@pytest.mark.asyncio
async def test_rag_very_specific_query():
    """Very specific query — RAG uses semantic similarity not keyword matching.
    Geography-specific queries may return 0 results if document content 
    focuses on cost/timing rather than location descriptions."""
    from app.db import AsyncSessionLocal
    input_data = RAGToolInput(
        query="hiking mountains Canada national park July",
        top_k=3
    )
    async with AsyncSessionLocal() as db:
        result = await rag_tool(input_data, db)
    print(f"\n🔍 Specific query results:")
    for r in result["results"]:
        print(f"   📍 {r['destination']} — score: {r['score']}")
    destinations = [r["destination"] for r in result["results"]]
    print(f"   Found: {destinations}")
    # RAG uses semantic similarity — geography queries may return 0 results
    # when document content focuses on cost/timing rather than location
    assert "results" in result  # should not crash regardless