from fastapi import APIRouter

from ..config import get_settings
from ..models.schemas import FeaturesResponse
from ..services.snowflake import get_snowflake_service

router = APIRouter(prefix="/api", tags=["features"])


@router.get("/features/{user_id}", response_model=FeaturesResponse)
async def get_user_features(user_id: str):
    """
    Get current feature values and embeddings for a user (debugging endpoint).

    This endpoint directly queries the Online Feature Serving layer
    to show the current state of user features including:
    - Raw features (click history, category preferences)
    - User embeddings (base, delta, combined)

    Useful for:
    - Debugging feature updates
    - Demonstrating low-latency feature retrieval
    - Visualizing embedding state in the UI
    """
    service = get_snowflake_service()
    settings = get_settings()

    features, latency = await service.get_user_features(user_id)

    return FeaturesResponse(
        user_id=user_id,
        features=features,
        source="mock" if settings.use_mock else "snowflake",
        latency_ms=latency,
    )
