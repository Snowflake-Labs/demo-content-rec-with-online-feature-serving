import { Header } from './components/Header';
import { ProductGrid } from './components/ProductGrid';
import { RecommendSection } from './components/RecommendSection';
import { FeatureDebugPanel } from './components/FeatureDebugPanel';
import { useRecommendation } from './hooks/useRecommendation';
import './App.css';

function App() {
  const {
    products,
    recommendations,
    scoredRecommendations,
    userFeatures,
    latencyMetrics,
    isLoading,
    isUpdating,
    error,
    handleProductClick,
  } = useRecommendation();

  return (
    <div className="app">
      <Header isUpdating={isUpdating} />

      <main className="main-content">
        <div className="container">
          {error && (
            <div className="error-banner">
              <p>{error}</p>
            </div>
          )}

          <RecommendSection
            recommendations={recommendations}
            scoredRecommendations={scoredRecommendations}
            featureLatency={latencyMetrics.featureServing}
            totalLatency={latencyMetrics.total}
            onProductClick={handleProductClick}
            isLoading={isLoading}
          />

          <ProductGrid
            products={products}
            recentClickIds={userFeatures?.recent_click_ids || []}
            onProductClick={handleProductClick}
          />
        </div>
      </main>

      <FeatureDebugPanel 
        features={userFeatures} 
        latencyMetrics={latencyMetrics}
      />

      <footer className="footer">
        <div className="container">
          <p>
            Powered by <strong>Snowflake Online Feature Serving</strong> —
            Two-Tower Model with Real-time Embedding Updates
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
