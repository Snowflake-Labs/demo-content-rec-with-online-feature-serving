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
Two-Tower DNN test script

Usage:
    cd backend
    uv run python test_two_tower.py
"""

import sys
sys.path.insert(0, '.')

from app.services.embeddings import (
    TwoTowerModel,
    compute_item_embedding,
    compute_user_base_embedding,
    compute_user_delta_embedding,
    get_user_embedding_from_tower,
    cosine_similarity,
    get_two_tower_model,
    EMBEDDING_DIM,
)
from app.models.schemas import Product


def test_item_tower():
    """Item Tower test"""
    print("=" * 60)
    print("1. Item Tower test")
    print("=" * 60)
    
    # Test products
    products = [
        Product(
            product_id="PROD001",
            name="Wireless Headphones",
            category="Electronics",
            price=299.99,
            rating=4.5,
            review_count=1250,
        ),
        Product(
            product_id="PROD002",
            name="Running Shoes",
            category="Sports",
            price=129.99,
            rating=4.3,
            review_count=890,
        ),
        Product(
            product_id="PROD003",
            name="Python Programming Book",
            category="Books",
            price=49.99,
            rating=4.8,
            review_count=2100,
        ),
    ]
    
    embeddings = {}
    for product in products:
        emb = compute_item_embedding(product)
        embeddings[product.product_id] = emb
        print(f"\n{product.name} ({product.category}):")
        print(f"  Embedding dim: {len(emb)}")
        print(f"  First 8 dims: {[round(x, 4) for x in emb[:8]]}")
        print(f"  L2 norm: {sum(x**2 for x in emb)**0.5:.4f}")
    
    # Calculate similarity scores between products
    print("\nSimilarity scores between products:")
    for i, p1 in enumerate(products):
        for p2 in products[i+1:]:
            sim = cosine_similarity(embeddings[p1.product_id], embeddings[p2.product_id])
            print(f"  {p1.name} vs {p2.name}: {sim:.4f}")


def test_user_tower():
    """User Tower test"""
    print("\n" + "=" * 60)
    print("2. User Tower test")
    print("=" * 60)
    
    # Test user (Electronics like)
    category_prefs = {"Electronics": 5, "Sports": 2, "Books": 1}
    total_clicks = 8
    
    # Base Embedding（History only）
    base_emb = compute_user_base_embedding(category_prefs, total_clicks)
    print(f"\nBase Embedding (履歴: {category_prefs}):")
    print(f"  Dim: {len(base_emb)}")
    print(f"  First 8 dims: {[round(x, 4) for x in base_emb[:8]]}")
    
    # Delta Embedding（Real-time）
    electronics_product = Product(
        product_id="PROD001",
        name="Wireless Headphones",
        category="Electronics",
        price=299.99,
        rating=4.5,
        review_count=1250,
    )
    item_emb = compute_item_embedding(electronics_product)
    
    # Click 1st time
    delta1 = compute_user_delta_embedding([], item_emb, decay_factor=0.7)
    print(f"\nDelta Embedding (1st click):")
    print(f"  First 8 dims: {[round(x, 4) for x in delta1[:8]]}")
    
    # Click 2nd time (same product)
    delta2 = compute_user_delta_embedding(delta1, item_emb, decay_factor=0.7)
    print(f"\nDelta Embedding (2nd click):")
    print(f"  First 8 dims: {[round(x, 4) for x in delta2[:8]]}")
    
    # User Tower からの Combined Embedding
    combined = get_user_embedding_from_tower(category_prefs, total_clicks, delta2)
    print(f"\nCombined Embedding (User Tower出力):")
    print(f"  Dim: {len(combined)}")
    print(f"  First 8 dims: {[round(x, 4) for x in combined[:8]]}")


def test_recommendation_scenario():
    """Recommendation scenario test"""
    print("\n" + "=" * 60)
    print("3. Recommendation scenario test")
    print("=" * 60)
    
    # 商品カタログ
    products = [
        Product(product_id="E1", name="Smartwatch", category="Electronics", price=399.99, rating=4.6, review_count=500),
        Product(product_id="E2", name="Wireless Earbuds", category="Electronics", price=199.99, rating=4.4, review_count=800),
        Product(product_id="S1", name="Running Shoes", category="Sports", price=129.99, rating=4.5, review_count=600),
        Product(product_id="S2", name="Yoga Mat", category="Sports", price=49.99, rating=4.2, review_count=400),
        Product(product_id="B1", name="Business Book", category="Books", price=29.99, rating=4.7, review_count=1200),
    ]
    
    # Item Embeddings
    item_embeddings = {p.product_id: compute_item_embedding(p) for p in products}
    
    # User: Electronics clicked 2 times
    print("\nScenario: User has clicked Electronics 2 times")
    
    category_prefs = {"Electronics": 2}
    total_clicks = 2
    
    # Simulate state with E1 clicked and delta updated
    delta = compute_user_delta_embedding([], item_embeddings["E1"], decay_factor=0.7)
    delta = compute_user_delta_embedding(delta, item_embeddings["E2"], decay_factor=0.7)
    
    # User Embedding
    user_emb = get_user_embedding_from_tower(category_prefs, total_clicks, delta)
    
    # Calculate similarity scores with products
    print("\nSimilarity scores with products:")
    scores = []
    for p in products:
        sim = cosine_similarity(user_emb, item_embeddings[p.product_id])
        scores.append((p, sim))
        print(f"  {p.name} ({p.category}): {sim:.4f}")
    
    # Ranking
    scores.sort(key=lambda x: x[1], reverse=True)
    print("\nRecommendation ranking:")
    for i, (p, sim) in enumerate(scores, 1):
        print(f"  {i}. {p.name} ({p.category}) - スコア: {sim:.4f}")


def test_model_weights():
    """Check model weights"""
    print("\n" + "=" * 60)
    print("4. Check model structure")
    print("=" * 60)
    
    model = get_two_tower_model()
    
    print("\nItem Tower structure:")
    for name, param in model.item_tower.named_parameters():
        print(f"  {name}: {param.shape}")
    
    print("\nUser Tower structure:")
    for name, param in model.user_tower.named_parameters():
        print(f"  {name}: {param.shape}")
    
    item_params = sum(p.numel() for p in model.item_tower.parameters())
    user_params = sum(p.numel() for p in model.user_tower.parameters())
    print(f"\nTotal parameters:")
    print(f"  Item Tower: {item_params:,}")
    print(f"  User Tower: {user_params:,}")
    print(f"  Total: {item_params + user_params:,}")


if __name__ == "__main__":
    print("Two-Tower DNN test")
    print(f"Embedding dimension: {EMBEDDING_DIM}")
    
    test_item_tower()
    test_user_tower()
    test_recommendation_scenario()
    test_model_weights()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
