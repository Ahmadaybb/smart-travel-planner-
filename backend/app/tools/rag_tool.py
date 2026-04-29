from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.retriever import retrieve

class RAGToolInput(BaseModel):
    query: str
    top_k: int = 4

async def rag_tool(input: RAGToolInput, db: AsyncSession) -> dict:
    results = await retrieve(input.query, db, input.top_k)
    
    if not results:
        return {"error": "No relevant documents found", "results": []}
    
    return {
        "results": results,
        "context": "\n\n".join([r["content"] for r in results])
    }