import pandas as pd
from pydantic import BaseModel, Field
from app.state import ml_model

class ClassifierToolInput(BaseModel):
    avg_cost_per_day_usd: float = Field(..., gt=0)
    avg_temp_july_celsius: float
    hiking_score: int = Field(..., ge=1, le=5)
    beach_score: int = Field(..., ge=1, le=5)
    museums_count: int = Field(..., ge=0)
    unesco_sites: int = Field(..., ge=0)
    tourist_density: int = Field(..., ge=1, le=5)
    family_friendly_score: int = Field(..., ge=1, le=5)
    safety_score: int = Field(..., ge=1, le=5)
    avg_meal_cost_usd: float = Field(..., gt=0)

FEATURES = [
    "avg_cost_per_day_usd",
    "avg_temp_july_celsius",
    "hiking_score",
    "beach_score",
    "museums_count",
    "unesco_sites",
    "tourist_density",
    "family_friendly_score",
    "safety_score",
    "avg_meal_cost_usd"
]

async def classifier_tool(input: ClassifierToolInput) -> dict:
    model = ml_model.get("classifier")
    if not model:
        return {"error": "ML model not loaded"}

    features = pd.DataFrame([input.model_dump()])[FEATURES]
    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    confidence = round(float(max(probabilities)), 4)

    return {
        "travel_style": prediction,
        "confidence": confidence
    }