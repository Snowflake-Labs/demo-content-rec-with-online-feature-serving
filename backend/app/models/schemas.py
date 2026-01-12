from datetime import datetime

from pydantic import BaseModel, Field

# Embedding dimension for Two-Tower model
EMBEDDING_DIM = 32  # Small for demo, production would use 128-256


class Product(BaseModel):
    """Product information schema."""

    product_id: str
    name: str
    category: str
    description: str | None = None
    price: float
    image_url: str | None = None
    rating: float = 4.0
    review_count: int = 0


class ProductWithEmbedding(Product):
    """Product with pre-computed embedding (Item Tower output)."""

    embedding: list[float] = Field(default_factory=list)


class UserFeatures(BaseModel):
    """User features from Feature Store."""

    user_id: str
    recent_click_ids: list[str] = Field(default_factory=list)
    category_preference: dict[str, int] = Field(default_factory=dict)
    total_clicks: int = 0
    last_click_timestamp: datetime | None = None


class UserEmbeddings(BaseModel):
    """User embeddings for Two-Tower model."""

    user_id: str
    base_embedding: list[float] = Field(default_factory=list)  # Batch computed
    delta_embedding: list[float] = Field(default_factory=list)  # Real-time updated
    combined_embedding: list[float] = Field(default_factory=list)  # Base + Delta


class UserFeaturesWithEmbedding(UserFeatures):
    """User features including embeddings."""

    embeddings: UserEmbeddings | None = None


class ClickEvent(BaseModel):
    """Click event request schema."""

    user_id: str
    product_id: str


class ClickEventResponse(BaseModel):
    """Response after recording a click event."""

    success: bool
    message: str
    updated_features: UserFeaturesWithEmbedding | None = None
    latency_ms: float = 0.0
    delta_update_ms: float = 0.0  # Time to update delta embedding


class ScoredProduct(BaseModel):
    """Product with similarity score."""

    product: Product
    similarity_score: float
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    """Recommendation response with products and metadata."""

    user_id: str
    recommendations: list[Product]
    scored_recommendations: list[ScoredProduct] = Field(default_factory=list)
    features_used: UserFeaturesWithEmbedding
    feature_serving_latency_ms: float = 0.0
    embedding_compute_ms: float = 0.0
    similarity_compute_ms: float = 0.0
    total_latency_ms: float = 0.0


class FeaturesResponse(BaseModel):
    """Response containing user features for debugging."""

    user_id: str
    features: UserFeaturesWithEmbedding
    source: str  # "snowflake" or "mock"
    latency_ms: float = 0.0
