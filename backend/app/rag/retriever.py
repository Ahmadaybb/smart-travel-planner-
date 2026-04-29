from app.state import embedder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def retrieve(query: str, db: AsyncSession, top_k: int = 4) -> list[dict]:
    try:
        query_vector = embedder["model"].encode(query).tolist()
        query_str = "[" + ",".join(map(str, query_vector)) + "]"

        result = await db.execute(
            text("""
                SELECT destination, content, source,
                       1 - (embedding <=> CAST(:query_vec AS vector)) AS score
                FROM documents
                ORDER BY embedding <=> CAST(:query_vec AS vector)
                LIMIT :top_k
            """),
            {"query_vec": query_str, "top_k": top_k}
        )

        rows = result.fetchall()
        return [
            {
                "destination": row.destination,
                "content": row.content,
                "source": row.source,
                "score": round(row.score, 4)
            }
            for row in rows
        ]
    except Exception as e:
        await db.rollback()
        return []