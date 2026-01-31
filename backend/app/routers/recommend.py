# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
