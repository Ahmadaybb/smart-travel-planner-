import pytest
from pydantic import ValidationError
from app.tools.classifier_tool import ClassifierToolInput
from app.tools.rag_tool import RAGToolInput
from app.tools.live_conditions_tool import LiveConditionsInput


# --- ClassifierToolInput ---

def test_classifier_valid_input():
    data = ClassifierToolInput(
        avg_cost_per_day_usd=100,
        avg_temp_july_celsius=25,
        hiking_score=4,
        beach_score=2,
        museums_count=5,
        unesco_sites=2,
        tourist_density=3,
        family_friendly_score=4,
        safety_score=5,
        avg_meal_cost_usd=15
    )
    assert data.hiking_score == 4


def test_classifier_invalid_hiking_score():
    with pytest.raises(ValidationError):
        ClassifierToolInput(
            avg_cost_per_day_usd=100,
            avg_temp_july_celsius=25,
            hiking_score=6,  # max is 5
            beach_score=2,
            museums_count=5,
            unesco_sites=2,
            tourist_density=3,
            family_friendly_score=4,
            safety_score=5,
            avg_meal_cost_usd=15
        )


def test_classifier_invalid_negative_cost():
    with pytest.raises(ValidationError):
        ClassifierToolInput(
            avg_cost_per_day_usd=-50,  # must be positive
            avg_temp_july_celsius=25,
            hiking_score=3,
            beach_score=2,
            museums_count=5,
            unesco_sites=2,
            tourist_density=3,
            family_friendly_score=4,
            safety_score=5,
            avg_meal_cost_usd=15
        )


def test_classifier_invalid_beach_score_zero():
    with pytest.raises(ValidationError):
        ClassifierToolInput(
            avg_cost_per_day_usd=100,
            avg_temp_july_celsius=25,
            hiking_score=3,
            beach_score=0,  # min is 1
            museums_count=5,
            unesco_sites=2,
            tourist_density=3,
            family_friendly_score=4,
            safety_score=5,
            avg_meal_cost_usd=15
        )


# --- RAGToolInput ---

def test_rag_valid_input():
    data = RAGToolInput(query="hiking in July", top_k=4)
    assert data.query == "hiking in July"


def test_rag_default_top_k():
    data = RAGToolInput(query="beach destinations")
    assert data.top_k == 4


# --- LiveConditionsInput ---

def test_live_conditions_valid():
    data = LiveConditionsInput(destination="Banff", country_code="CA")
    assert data.destination == "Banff"


def test_live_conditions_missing_destination():
    with pytest.raises(ValidationError):
        LiveConditionsInput(country_code="CA")  # destination required