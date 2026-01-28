from fastapi import APIRouter, Query

from ..models.schemas import RecommendationResponse
from ..services.recommender import get_recommender_service

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.get("/recommend/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: str,
    limit: int = Query(default=6, ge=1, le=20, description="Number of recommendations"),
):
    """
    Get personalized product recommendations for a user.

    This endpoint:
    1. Fetches user features via Online Feature Serving (low latency)
    2. Uses the recommendation algorithm to score products
    3. Returns top-N recommendations with latency metrics
    """
    service = get_recommender_service()

    recommendations = await service.get_recommendations(user_id=user_id, limit=limit)

    return recommendations
