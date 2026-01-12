"""
Two-Tower DNN for recommendation embeddings.

Architecture:
┌─────────────────────────────────────────────────────────────────────┐
│                      Two-Tower Deep Neural Network                   │
├─────────────────────────────────┬───────────────────────────────────┤
│          User Tower             │           Item Tower              │
│                                 │                                   │
│   Input: User Features          │   Input: Item Features            │
│   - category_prefs (5-dim)      │   - category (5-dim one-hot)      │
│   - total_clicks (1-dim)        │   - price (1-dim)                 │
│   - delta_embedding (32-dim)    │   - rating (1-dim)                │
│                                 │   - popularity (1-dim)            │
│         ↓                       │         ↓                         │
│   [Linear 38 → 64]              │   [Linear 8 → 64]                 │
│   [ReLU]                        │   [ReLU]                          │
│   [Linear 64 → 64]              │   [Linear 64 → 64]                │
│   [ReLU]                        │   [ReLU]                          │
│   [Linear 64 → 32]              │   [Linear 64 → 32]                │
│   [L2 Normalize]                │   [L2 Normalize]                  │
│         ↓                       │         ↓                         │
│   User Embedding (32-dim)       │   Item Embedding (32-dim)         │
└─────────────────────────────────┴───────────────────────────────────┘
                    ↓                           ↓
              Cosine Similarity = dot(user_emb, item_emb)
"""

import math
from functools import lru_cache

import torch
import torch.nn as nn

from ..models.schemas import (
    EMBEDDING_DIM,
    Product,
    ProductWithEmbedding,
    UserEmbeddings,
)

# Categories for encoding
CATEGORIES = ["Electronics", "Fashion", "Home", "Sports", "Books"]
CATEGORY_TO_IDX = {cat: idx for idx, cat in enumerate(CATEGORIES)}
NUM_CATEGORIES = len(CATEGORIES)

# Feature dimensions
ITEM_INPUT_DIM = NUM_CATEGORIES + 3  # category one-hot (5) + price + rating + popularity
USER_INPUT_DIM = NUM_CATEGORIES + 1 + EMBEDDING_DIM  # category prefs (5) + clicks (1) + delta (32)
HIDDEN_DIM = 64


class ItemTower(nn.Module):
    """
    Item Tower: Maps item features to embedding space.

    Input: [category_one_hot (5), price (1), rating (1), popularity (1)] = 8 dims
    Output: 32-dimensional normalized embedding
    """

    def __init__(
        self,
        input_dim: int = ITEM_INPUT_DIM,
        hidden_dim: int = HIDDEN_DIM,
        output_dim: int = EMBEDDING_DIM,
    ):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        embedding = self.network(x)
        # L2 normalize
        return nn.functional.normalize(embedding, p=2, dim=-1)


class UserTower(nn.Module):
    """
    User Tower: Maps user features to embedding space.

    Input: [category_prefs (5), total_clicks (1), delta_embedding (32)] = 38 dims
    Output: 32-dimensional normalized embedding
    """

    def __init__(
        self,
        input_dim: int = USER_INPUT_DIM,
        hidden_dim: int = HIDDEN_DIM,
        output_dim: int = EMBEDDING_DIM,
    ):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        embedding = self.network(x)
        # L2 normalize
        return nn.functional.normalize(embedding, p=2, dim=-1)


class TwoTowerModel:
    """
    Two-Tower recommendation model with pre-initialized weights.

    In production, these weights would be trained on click data.
    For demo, we use deterministically initialized weights.
    """

    def __init__(self):
        # Set seed for reproducible weights
        torch.manual_seed(42)

        self.item_tower = ItemTower()
        self.user_tower = UserTower()

        # Initialize with Xavier for better gradient flow
        self._init_weights(self.item_tower)
        self._init_weights(self.user_tower)

        # Set to eval mode (no dropout, etc.)
        self.item_tower.eval()
        self.user_tower.eval()

    def _init_weights(self, module: nn.Module):
        """Initialize weights using Xavier initialization."""
        for m in module.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def compute_item_embedding(self, product: Product) -> list[float]:
        """Compute item embedding using Item Tower DNN."""
        # Prepare input features
        features = self._prepare_item_features(product)

        with torch.no_grad():
            input_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
            embedding = self.item_tower(input_tensor)
            return embedding.squeeze(0).tolist()

    def compute_user_embedding(
        self, category_preference: dict[str, int], total_clicks: int, delta_embedding: list[float]
    ) -> list[float]:
        """Compute user embedding using User Tower DNN."""
        # Prepare input features
        features = self._prepare_user_features(category_preference, total_clicks, delta_embedding)

        with torch.no_grad():
            input_tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
            embedding = self.user_tower(input_tensor)
            return embedding.squeeze(0).tolist()

    def _prepare_item_features(self, product: Product) -> list[float]:
        """Convert product to feature vector for Item Tower."""
        features = []

        # Category one-hot (5 dims)
        cat_idx = CATEGORY_TO_IDX.get(product.category, 0)
        for i in range(NUM_CATEGORIES):
            features.append(1.0 if i == cat_idx else 0.0)

        # Price normalized (1 dim) - assume range 0-1000
        features.append(min(product.price / 1000.0, 1.0))

        # Rating normalized (1 dim) - range 1-5 → 0-1
        features.append((product.rating - 1.0) / 4.0)

        # Popularity - log normalized (1 dim)
        features.append(min(math.log1p(product.review_count) / 10.0, 1.0))

        return features

    def _prepare_user_features(
        self, category_preference: dict[str, int], total_clicks: int, delta_embedding: list[float]
    ) -> list[float]:
        """Convert user data to feature vector for User Tower."""
        features = []

        # Category preferences normalized (5 dims)
        if total_clicks > 0:
            for cat in CATEGORIES:
                count = category_preference.get(cat, 0)
                features.append(count / total_clicks)
        else:
            features.extend([0.0] * NUM_CATEGORIES)

        # Total clicks normalized (1 dim) - log scale
        features.append(min(math.log1p(total_clicks) / 10.0, 1.0))

        # Delta embedding (32 dims) - captures recent behavior
        if delta_embedding and len(delta_embedding) == EMBEDDING_DIM:
            features.extend(delta_embedding)
        else:
            features.extend([0.0] * EMBEDDING_DIM)

        return features


# Singleton model instance
@lru_cache(maxsize=1)
def get_two_tower_model() -> TwoTowerModel:
    """Get singleton Two-Tower model instance."""
    return TwoTowerModel()


def compute_item_embedding(product: Product) -> list[float]:
    """
    Compute item embedding using Two-Tower DNN (Item Tower).

    This function is used in both production and demo environments.

    Args:
        product: Product object with attributes

    Returns:
        32-dimensional L2-normalized embedding vector
    """
    model = get_two_tower_model()
    return model.compute_item_embedding(product)


def compute_user_base_embedding(
    category_preference: dict[str, int], total_clicks: int
) -> list[float]:
    """
    Compute user base embedding using Two-Tower DNN (User Tower).

    This is computed without delta (historical preferences only).
    In production, this would be computed daily as a batch job.

    Args:
        category_preference: Dict mapping category names to click counts
        total_clicks: Total number of clicks by the user

    Returns:
        32-dimensional L2-normalized embedding vector
    """
    model = get_two_tower_model()
    # Base embedding uses zero delta (only historical preferences)
    zero_delta = [0.0] * EMBEDDING_DIM
    return model.compute_user_embedding(category_preference, total_clicks, zero_delta)


def compute_user_delta_embedding(
    current_delta: list[float], clicked_item_embedding: list[float], decay_factor: float = 0.7
) -> list[float]:
    """
    Update user delta embedding with exponential moving average (EMA).

    This captures the user's REAL-TIME interests based on recent clicks.

    Formula: new_delta = decay_factor * current_delta + (1 - decay_factor) * item_embedding

    Args:
        current_delta: Current delta embedding (or empty for first click)
        clicked_item_embedding: Embedding of the just-clicked item
        decay_factor: Weight for historical delta (default 0.7)

    Returns:
        32-dimensional L2-normalized embedding vector
    """
    if not current_delta:
        current_delta = [0.0] * EMBEDDING_DIM

    new_delta = []
    for i in range(EMBEDDING_DIM):
        new_val = decay_factor * current_delta[i] + (1 - decay_factor) * clicked_item_embedding[i]
        new_delta.append(new_val)

    return l2_normalize(new_delta)


def combine_user_embeddings(
    base_embedding: list[float], delta_embedding: list[float], base_weight: float = 0.6
) -> list[float]:
    """
    Combine base and delta embeddings using User Tower DNN.

    The User Tower takes both historical preferences AND delta embedding
    as input, producing a unified user representation.

    Args:
        base_embedding: User's long-term preference embedding (not directly used)
        delta_embedding: User's real-time session embedding
        base_weight: Not used in DNN approach (kept for API compatibility)

    Returns:
        32-dimensional L2-normalized embedding vector from User Tower
    """
    # In DNN approach, we don't manually combine - the User Tower does it
    # But we need category preferences which we don't have here
    # So we use weighted average as fallback
    if not base_embedding:
        base_embedding = [0.0] * EMBEDDING_DIM
    if not delta_embedding:
        delta_embedding = [0.0] * EMBEDDING_DIM

    combined = []
    delta_weight = 1 - base_weight
    for i in range(EMBEDDING_DIM):
        combined.append(base_weight * base_embedding[i] + delta_weight * delta_embedding[i])

    return l2_normalize(combined)


def get_user_embedding_from_tower(
    category_preference: dict[str, int], total_clicks: int, delta_embedding: list[float]
) -> list[float]:
    """
    Get user embedding directly from User Tower DNN.

    This is the preferred method as it uses the full DNN.

    Args:
        category_preference: Dict of category click counts
        total_clicks: Total clicks by user
        delta_embedding: Current delta embedding

    Returns:
        32-dimensional L2-normalized embedding vector
    """
    model = get_two_tower_model()
    return model.compute_user_embedding(category_preference, total_clicks, delta_embedding)


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Since vectors are L2-normalized, this equals the dot product.

    Args:
        vec_a: First embedding vector
        vec_b: Second embedding vector

    Returns:
        Similarity score in range [-1, 1], where 1 = most similar
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def l2_normalize(vec: list[float]) -> list[float]:
    """L2 normalize a vector to unit length."""
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def compute_all_item_embeddings(products: list[Product]) -> dict[str, ProductWithEmbedding]:
    """
    Pre-compute embeddings for all products using Item Tower DNN.

    In production, this would run as a scheduled batch job.

    Args:
        products: List of all products

    Returns:
        Dict mapping product_id to ProductWithEmbedding
    """
    result = {}
    for product in products:
        embedding = compute_item_embedding(product)
        result[product.product_id] = ProductWithEmbedding(
            **product.model_dump(), embedding=embedding
        )
    return result


def get_user_embeddings(
    user_id: str,
    category_preference: dict[str, int],
    total_clicks: int,
    current_delta: list[float] | None = None,
) -> UserEmbeddings:
    """
    Get complete user embeddings using Two-Tower DNN.

    Args:
        user_id: User identifier
        category_preference: Dict of category click counts
        total_clicks: Total clicks by user
        current_delta: Current delta embedding (optional)

    Returns:
        UserEmbeddings with base, delta, and combined embeddings
    """
    delta = current_delta if current_delta else [0.0] * EMBEDDING_DIM

    # Base embedding (without delta influence)
    base = compute_user_base_embedding(category_preference, total_clicks)

    # Combined embedding from User Tower (with delta as input)
    combined = get_user_embedding_from_tower(category_preference, total_clicks, delta)

    return UserEmbeddings(
        user_id=user_id, base_embedding=base, delta_embedding=delta, combined_embedding=combined
    )
