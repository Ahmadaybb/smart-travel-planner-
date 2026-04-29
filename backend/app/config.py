from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Groq
    GROQ_API_KEY: str
    GROQ_CHEAP_MODEL: str = "llama-3.1-8b-instant"
    GROQ_STRONG_MODEL: str = "llama-3.3-70b-versatile"
    
    # Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Webhook
    WEBHOOK_URL: str

    #model path
    ML_MODEL_PATH: str = "app/ml/travel_classifier.joblib"
    
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()