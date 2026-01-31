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

from ..models.schemas import Product
from ..services.snowflake import get_snowflake_service

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products", response_model=list[Product])
async def get_all_products(category: str | None = None):
    """
    Get all products from the catalog.

    Optionally filter by category.
    """
    service = get_snowflake_service()
    products = await service.get_all_products()

    if category:
        products = [p for p in products if p.category.lower() == category.lower()]

    return products


@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """
    Get a single product by ID.
    """
    service = get_snowflake_service()
    product = await service.get_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    return product


@router.get("/categories", response_model=list[str])
async def get_categories():
    """
    Get all unique product categories.
    """
    service = get_snowflake_service()
    products = await service.get_all_products()

    categories = sorted(set(p.category for p in products))
    return categories
