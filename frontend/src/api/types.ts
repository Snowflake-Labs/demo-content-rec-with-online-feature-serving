export interface Product {
  product_id: string;
  name: string;
  category: string;
  description: string | null;
  price: number;
  image_url: string | null;
  rating: number;
  review_count: number;
}

export interface UserEmbeddings {
  user_id: string;
  base_embedding: number[];
  delta_embedding: number[];
  combined_embedding: number[];
}

export interface UserFeatures {
  user_id: string;
  recent_click_ids: string[];
  category_preference: Record<string, number>;
  total_clicks: number;
  last_click_timestamp: string | null;
  embeddings: UserEmbeddings | null;
}

export interface ClickEvent {
  user_id: string;
  product_id: string;
}

export interface ClickEventResponse {
  success: boolean;
  message: string;
  updated_features: UserFeatures | null;
  latency_ms: number;
  delta_update_ms: number;
}

export interface ScoredProduct {
  product: Product;
  similarity_score: number;
  score_breakdown: Record<string, number>;
}

export interface RecommendationResponse {
  user_id: string;
  recommendations: Product[];
  scored_recommendations: ScoredProduct[];
  features_used: UserFeatures;
  feature_serving_latency_ms: number;
  embedding_compute_ms: number;
  similarity_compute_ms: number;
  total_latency_ms: number;
}

export interface FeaturesResponse {
  user_id: string;
  features: UserFeatures;
  source: 'snowflake' | 'mock';
  latency_ms: number;
}
