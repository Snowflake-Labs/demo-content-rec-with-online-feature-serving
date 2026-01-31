// Copyright 2026 Snowflake Inc.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { useState, useCallback, useEffect } from 'react';
import { apiClient } from '../api/client';
import type {
  Product,
  UserFeatures,
  ScoredProduct,
} from '../api/types';

interface LatencyMetrics {
  featureServing: number;
  embeddingCompute: number;
  similarityCompute: number;
  total: number;
  deltaUpdate: number;
}

interface UseRecommendationReturn {
  products: Product[];
  recommendations: Product[];
  scoredRecommendations: ScoredProduct[];
  userFeatures: UserFeatures | null;
  latencyMetrics: LatencyMetrics;
  isLoading: boolean;
  isUpdating: boolean;
  error: string | null;
  handleProductClick: (productId: string) => Promise<void>;
  refreshRecommendations: () => Promise<void>;
}

const DEFAULT_USER_ID = 'demo_user';

const initialLatencyMetrics: LatencyMetrics = {
  featureServing: 0,
  embeddingCompute: 0,
  similarityCompute: 0,
  total: 0,
  deltaUpdate: 0,
};

export function useRecommendation(): UseRecommendationReturn {
  const [products, setProducts] = useState<Product[]>([]);
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [scoredRecommendations, setScoredRecommendations] = useState<ScoredProduct[]>([]);
  const [userFeatures, setUserFeatures] = useState<UserFeatures | null>(null);
  const [latencyMetrics, setLatencyMetrics] = useState<LatencyMetrics>(initialLatencyMetrics);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load initial products
  useEffect(() => {
    const loadProducts = async () => {
      try {
        const allProducts = await apiClient.getProducts();
        setProducts(allProducts);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load products');
      }
    };
    loadProducts();
  }, []);

  // Refresh recommendations
  const refreshRecommendations = useCallback(async () => {
    try {
      const response = await apiClient.getRecommendations(DEFAULT_USER_ID, 6);
      setRecommendations(response.recommendations);
      setScoredRecommendations(response.scored_recommendations);
      setUserFeatures(response.features_used);
      setLatencyMetrics(prev => ({
        ...prev,
        featureServing: response.feature_serving_latency_ms,
        embeddingCompute: response.embedding_compute_ms,
        similarityCompute: response.similarity_compute_ms,
        total: response.total_latency_ms,
      }));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load recommendations');
    }
  }, []);

  // Load initial recommendations
  useEffect(() => {
    const init = async () => {
      setIsLoading(true);
      await refreshRecommendations();
      setIsLoading(false);
    };
    init();
  }, [refreshRecommendations]);

  // Handle product click
  const handleProductClick = useCallback(async (productId: string) => {
    setIsUpdating(true);
    try {
      // Record click and update features + embeddings
      const clickResponse = await apiClient.recordClick({
        user_id: DEFAULT_USER_ID,
        product_id: productId,
      });

      // Update local features state immediately
      if (clickResponse.updated_features) {
        setUserFeatures(clickResponse.updated_features);
        setLatencyMetrics(prev => ({
          ...prev,
          deltaUpdate: clickResponse.delta_update_ms,
        }));
      }

      // Refresh recommendations with new embeddings
      await refreshRecommendations();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record click');
    } finally {
      setIsUpdating(false);
    }
  }, [refreshRecommendations]);

  return {
    products,
    recommendations,
    scoredRecommendations,
    userFeatures,
    latencyMetrics,
    isLoading,
    isUpdating,
    error,
    handleProductClick,
    refreshRecommendations,
  };
}
