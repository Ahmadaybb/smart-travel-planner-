from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import engine
from app.models.database import Base
import joblib
from app.config import get_settings
from app.routes.auth import router as auth_router
from app.routes.agent import router as agent_router
from app.state import ml_model, embedder
from sentence_transformers import SentenceTransformer
from sqlalchemy import text

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    ml_model["classifier"] = joblib.load(settings.ML_MODEL_PATH)
    embedder["model"] = SentenceTransformer("all-MiniLM-L6-v2")
    print("ML model and embedder loaded")

    yield

    await engine.dispose()
    print("DB connection closed")

app = FastAPI(lifespan=lifespan)

# CORS must be added before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(agent_router)

@app.get("/health")
async def health():
    return {"status": "ok"}