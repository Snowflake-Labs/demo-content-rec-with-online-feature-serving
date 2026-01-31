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

"""
Two-Tower Recommendation Service.

Uses cosine similarity between user embeddings and item embeddings
to generate personalized recommendations.
"""

import time
from functools import lru_cache

from ..models.schemas import (
    Product,
    RecommendationResponse,
    ScoredProduct,
)
from .embeddings import cosine_similarity
from .snowflake import SnowflakeService, get_snowflake_service


class RecommenderService:
    """Service for generating product recommendations using Two-Tower model."""

    def __init__(self, snowflake_service: SnowflakeService):
        self.snowflake_service = snowflake_service

    async def get_recommendations(self, user_id: str, limit: int = 6) -> RecommendationResponse:
        """
        Get personalized recommendations using Two-Tower architecture.

        Strategy:
        1. Get user embeddings from Online Feature Serving
        2. Compute cosine similarity with all item embeddings
        3. Rank by similarity score
        4. Exclude recently clicked products
        5. Return top-N recommendations
        """
        start_time = time.time()

        # Get user features with embeddings (Online Feature Serving)
        features, feature_latency = await self.snowflake_service.get_user_features(user_id)

        # Get all item embeddings (pre-computed in production)
        embedding_start = time.time()
        item_embeddings = await self.snowflake_service.get_all_item_embeddings()
        embedding_latency = (time.time() - embedding_start) * 1000

        # Get user's combined embedding
        user_embedding = []
        if features.embeddings:
            user_embedding = features.embeddings.combined_embedding

        # Exclude recently clicked products
        recent_clicks_set = set(features.recent_click_ids)

        # Compute similarity scores
        similarity_start = time.time()
        scored_products: list[ScoredProduct] = []

        for product_id, item_with_embedding in item_embeddings.items():
            if product_id in recent_clicks_set:
                continue

            # Compute cosine similarity
            similarity = cosine_similarity(user_embedding, item_with_embedding.embedding)

            # Add small boost for highly rated products
            rating_boost = item_with_embedding.rating / 50  # 0.02-0.1 boost

            # Final score
            final_score = similarity + rating_boost

            # Create product without embedding for response
            product = Product(
                product_id=item_with_embedding.product_id,
                name=item_with_embedding.name,
                category=item_with_embedding.category,
                description=item_with_embedding.description,
                price=item_with_embedding.price,
                image_url=item_with_embedding.image_url,
                rating=item_with_embedding.rating,
                review_count=item_with_embedding.review_count,
            )

            scored_products.append(
                ScoredProduct(
                    product=product,
                    similarity_score=final_score,
                    score_breakdown={
                        "cosine_similarity": round(similarity, 4),
                        "rating_boost": round(rating_boost, 4),
                        "final_score": round(final_score, 4),
                    },
                )
            )

        # Sort by score (descending)
        scored_products.sort(key=lambda x: x.similarity_score, reverse=True)

        similarity_latency = (time.time() - similarity_start) * 1000

        # Get top recommendations
        top_scored = scored_products[:limit]
        recommendations = [sp.product for sp in top_scored]

        # If not enough recommendations (cold start), fill with popular products
        if len(recommendations) < limit:
            rec_ids = {p.product_id for p in recommendations}
            all_products = await self.snowflake_service.get_all_products()

            for product in sorted(all_products, key=lambda p: p.review_count, reverse=True):
                if (
                    product.product_id not in rec_ids
                    and product.product_id not in recent_clicks_set
                ):
                    recommendations.append(product)
                    top_scored.append(
                        ScoredProduct(
                            product=product, similarity_score=0.0, score_breakdown={"fallback": 1.0}
                        )
                    )
                    if len(recommendations) >= limit:
                        break

        total_latency = (time.time() - start_time) * 1000

        return RecommendationResponse(
            user_id=user_id,
            recommendations=recommendations,
            scored_recommendations=top_scored[:limit],
            features_used=features,
            feature_serving_latency_ms=feature_latency,
            embedding_compute_ms=embedding_latency,
            similarity_compute_ms=similarity_latency,
            total_latency_ms=total_latency,
        )


@lru_cache
def get_recommender_service() -> RecommenderService:
    """Get singleton RecommenderService instance."""
    return RecommenderService(get_snowflake_service())
