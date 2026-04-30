from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")
    
    # Database
    DATABASE_URL: str
    # Groq
    GROQ_API_KEY: str
    GROQ_CHEAP_MODEL: str = "llama3-8b-8192"
    GROQ_STRONG_MODEL: str = "llama3-70b-8192"
    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Webhook
    WEBHOOK_URL: str
    # ML Model
    ML_MODEL_PATH: str = "app/ml/travel_classifier.joblib"

    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "smart-travel-planner"
    LANGSMITH_ENDPOINT: str = "=https://api.smith.langchain.com"

@lru_cache
def get_settings() -> Settings:
    return Settings()