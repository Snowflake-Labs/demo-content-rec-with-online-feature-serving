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
