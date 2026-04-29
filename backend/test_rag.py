import asyncio
from sqlalchemy import text
from app.db import AsyncSessionLocal
from app.state import embedder
from sentence_transformers import SentenceTransformer

async def test():
    embedder["model"] = SentenceTransformer("all-MiniLM-L6-v2")
    
    async with AsyncSessionLocal() as db:
        # Test raw vector search
        query = "hiking destinations"
        query_vector = embedder["model"].encode(query).tolist()
        query_str = "[" + ",".join(map(str, query_vector)) + "]"
        
        print(f"Vector length: {len(query_vector)}")
        print(f"Query string preview: {query_str[:100]}")
        
        try:
            result = await db.execute(
                text("""
                    SELECT destination, content,
                           1 - (embedding <=> :query_vec AS vector) AS score
                    FROM documents
                    ORDER BY embedding <=> :query_vec AS vector
                    LIMIT 3
                """),
                {"query_vec": query_str}
            )
            rows = result.fetchall()
            print(f"Found: {len(rows)} results")
            for row in rows:
                print(f"  {row.destination} - score: {row.score}")
        except Exception as e:
            print(f"Search error: {e}")

asyncio.run(test())