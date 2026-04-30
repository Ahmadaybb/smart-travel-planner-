import asyncio
from app.db import AsyncSessionLocal
from app.state import ml_model, embedder
from sentence_transformers import SentenceTransformer
import joblib
from app.config import get_settings

settings = get_settings()

async def test():
    # Load models manually like lifespan does
    ml_model["classifier"] = joblib.load(settings.ML_MODEL_PATH)
    embedder["model"] = SentenceTransformer("all-MiniLM-L6-v2")
    print("Models loaded")

    async with AsyncSessionLocal() as db:
        from app.agent.agent import run_agent
        
        query = "I have 2 weeks in July and $700. I like swimimg. Where should I go?"
        print(f"Query: {query}\n")
        
        result = await run_agent(query, db)
        
        print("=== TOOL CALLS ===")
        for tool in result["tool_calls"]:
            print(f"\nTool: {tool['tool_name']}")
            print(f"Input: {tool['tool_input']}")
            print(f"Output: {tool['tool_output'][:200]}")
        
        print("\n=== ANSWER ===")
        print(result["answer"])
        
        print("\n=== TOKEN USAGE ===")
        print(result["token_usage"])

asyncio.run(test())