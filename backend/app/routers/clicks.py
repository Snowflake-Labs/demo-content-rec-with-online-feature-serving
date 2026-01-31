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

from fastapi import APIRouter, HTTPException

from ..models.schemas import ClickEvent, ClickEventResponse
from ..services.snowflake import get_snowflake_service

router = APIRouter(prefix="/api", tags=["clicks"])


@router.post("/click", response_model=ClickEventResponse)
async def record_click(event: ClickEvent):
    """
    Record a user click event and immediately update features + embeddings.

    This endpoint:
    1. Records the click in the CLICK_EVENTS table
    2. Updates USER_FEATURES with the new click data
    3. Updates user delta embedding in real-time (Two-Tower)
    4. Returns the updated features + embeddings for immediate UI feedback
    """
    service = get_snowflake_service()

    try:
        updated_features, latency, delta_latency = await service.record_click_and_update_features(
            user_id=event.user_id, product_id=event.product_id
        )

        return ClickEventResponse(
            success=True,
            message=f"Click recorded for product {event.product_id}",
            updated_features=updated_features,
            latency_ms=latency,
            delta_update_ms=delta_latency,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording click: {str(e)}")
