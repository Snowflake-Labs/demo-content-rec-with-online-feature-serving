import type {
  Product,
  ClickEvent,
  ClickEventResponse,
  RecommendationResponse,
  FeaturesResponse,
} from './types';

const API_BASE = '/api';

class ApiClient {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  }

  // Products
  async getProducts(category?: string): Promise<Product[]> {
    const params = category ? `?category=${encodeURIComponent(category)}` : '';
    return this.request<Product[]>(`/products${params}`);
  }

  async getProduct(productId: string): Promise<Product> {
    return this.request<Product>(`/products/${productId}`);
  }

  async getCategories(): Promise<string[]> {
    return this.request<string[]>('/categories');
  }

  // Clicks
  async recordClick(event: ClickEvent): Promise<ClickEventResponse> {
    return this.request<ClickEventResponse>('/click', {
      method: 'POST',
      body: JSON.stringify(event),
    });
  }

  // Recommendations
  async getRecommendations(
    userId: string,
    limit: number = 6
  ): Promise<RecommendationResponse> {
    return this.request<RecommendationResponse>(
      `/recommend/${userId}?limit=${limit}`
    );
  }

  // Features (debug)
  async getFeatures(userId: string): Promise<FeaturesResponse> {
    return this.request<FeaturesResponse>(`/features/${userId}`);
  }
}

export const apiClient = new ApiClient();
