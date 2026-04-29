import json
import asyncio
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.database import Document, Base
from app.config import get_settings

settings = get_settings()

# Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")  # 384 dimensions

async def ingest():
    # Load JSON
    data_path = Path("app/rag/rag_travel_dataset_enriched_60.json")
    with open(data_path) as f:
        documents = json.load(f)

    # Setup DB
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

    async with AsyncSession() as session:
        for doc in documents:
            # Generate embedding
            embedding = embedder.encode(doc["content"]).tolist()

            record = Document(
                destination=doc["destination"],
                content=doc["content"],
                embedding=embedding,
                source=doc.get("source", "unknown")
            )
            session.add(record)

        await session.commit()
        print(f"Ingested {len(documents)} documents")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(ingest())