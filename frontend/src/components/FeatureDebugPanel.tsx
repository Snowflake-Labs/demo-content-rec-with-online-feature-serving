import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { UserFeatures } from '../api/types';
import styles from './FeatureDebugPanel.module.css';

interface FeatureDebugPanelProps {
  features: UserFeatures | null;
  latencyMetrics?: {
    featureServing: number;
    embeddingCompute: number;
    similarityCompute: number;
    total: number;
    deltaUpdate: number;
  };
}

const categoryColors: Record<string, string> = {
  Electronics: 'var(--cat-electronics)',
  Fashion: 'var(--cat-fashion)',
  Home: 'var(--cat-home)',
  Sports: 'var(--cat-sports)',
  Books: 'var(--cat-books)',
};

// Visualize embedding as a heatmap row
function EmbeddingViz({ embedding, label }: { embedding: number[]; label: string }) {
  if (!embedding || embedding.length === 0) return null;
  
  // Take first 16 dimensions for visualization
  const dims = embedding.slice(0, 16);
  const maxVal = Math.max(...dims.map(Math.abs), 0.001);
  
  return (
    <div className={styles.embeddingRow}>
      <span className={styles.embeddingLabel}>{label}</span>
      <div className={styles.embeddingGrid}>
        {dims.map((val, idx) => {
          const normalized = val / maxVal;
          const intensity = Math.abs(normalized);
          const hue = normalized >= 0 ? 15 : 220; // Orange for positive, blue for negative
          return (
            <motion.div
              key={idx}
              className={styles.embeddingCell}
              initial={{ opacity: 0 }}
              animate={{ 
                opacity: 1,
                backgroundColor: `hsla(${hue}, 80%, 50%, ${intensity * 0.8 + 0.1})`
              }}
              transition={{ duration: 0.3 }}
              title={`dim[${idx}]: ${val.toFixed(3)}`}
            />
          );
        })}
      </div>
    </div>
  );
}

export function FeatureDebugPanel({ features, latencyMetrics }: FeatureDebugPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [activeTab, setActiveTab] = useState<'features' | 'embeddings' | 'latency'>('features');

  const totalPreference = features
    ? Object.values(features.category_preference).reduce((a, b) => a + b, 0)
    : 0;

  return (
    <motion.aside
      className={styles.panel}
      initial={{ x: 100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ delay: 0.5 }}
    >
      <button
        className={styles.toggleButton}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          style={{ transform: isExpanded ? 'rotate(0deg)' : 'rotate(180deg)' }}
        >
          <path
            d="M12 15L7 10L12 5"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            className={styles.content}
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 300, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className={styles.header}>
              <h3 className={styles.title}>Two-Tower Debug</h3>
              <span className={styles.badge}>Live</span>
            </div>

            {/* Tab Navigation */}
            <div className={styles.tabs}>
              <button
                className={`${styles.tab} ${activeTab === 'features' ? styles.activeTab : ''}`}
                onClick={() => setActiveTab('features')}
              >
                Features
              </button>
              <button
                className={`${styles.tab} ${activeTab === 'embeddings' ? styles.activeTab : ''}`}
                onClick={() => setActiveTab('embeddings')}
              >
                Embeddings
              </button>
              <button
                className={`${styles.tab} ${activeTab === 'latency' ? styles.activeTab : ''}`}
                onClick={() => setActiveTab('latency')}
              >
                Latency
              </button>
            </div>

            {!features ? (
              <div className={styles.empty}>
                <p>No features loaded</p>
              </div>
            ) : (
              <div className={styles.sections}>
                {/* Features Tab */}
                {activeTab === 'features' && (
                  <>
                    {/* User ID */}
                    <div className={styles.section}>
                      <h4 className={styles.sectionTitle}>User ID</h4>
                      <code className={styles.userId}>{features.user_id}</code>
                    </div>

                    {/* Stats */}
                    <div className={styles.section}>
                      <h4 className={styles.sectionTitle}>Stats</h4>
                      <div className={styles.stats}>
                        <div className={styles.stat}>
                          <span className={styles.statValue}>{features.total_clicks}</span>
                          <span className={styles.statLabel}>Clicks</span>
                        </div>
                        <div className={styles.stat}>
                          <span className={styles.statValue}>
                            {features.recent_click_ids.length}
                          </span>
                          <span className={styles.statLabel}>Recent</span>
                        </div>
                      </div>
                    </div>

                    {/* Category Preferences */}
                    <div className={styles.section}>
                      <h4 className={styles.sectionTitle}>Category Preferences</h4>
                      <div className={styles.preferences}>
                        {Object.entries(features.category_preference)
                          .sort(([, a], [, b]) => b - a)
                          .map(([category, count]) => {
                            const percentage = totalPreference > 0
                              ? (count / totalPreference) * 100
                              : 0;
                            const color = categoryColors[category] || 'var(--accent-primary)';
                            
                            return (
                              <motion.div
                                key={category}
                                className={styles.preference}
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                layout
                              >
                                <div className={styles.prefHeader}>
                                  <span
                                    className={styles.prefCategory}
                                    style={{ color }}
                                  >
                                    {category}
                                  </span>
                                  <span className={styles.prefCount}>{count}</span>
                                </div>
                                <div className={styles.prefBarTrack}>
                                  <motion.div
                                    className={styles.prefBar}
                                    style={{ backgroundColor: color }}
                                    initial={{ width: 0 }}
                                    animate={{ width: `${percentage}%` }}
                                    transition={{ duration: 0.5, ease: 'easeOut' }}
                                  />
                                </div>
                              </motion.div>
                            );
                          })}
                        
                        {Object.keys(features.category_preference).length === 0 && (
                          <p className={styles.emptyPrefs}>
                            Click products to build preferences
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Recent Clicks */}
                    <div className={styles.section}>
                      <h4 className={styles.sectionTitle}>Recent Clicks</h4>
                      <div className={styles.recentClicks}>
                        {features.recent_click_ids.length > 0 ? (
                          features.recent_click_ids.slice(0, 5).map((id, index) => (
                            <motion.code
                              key={`${id}-${index}`}
                              className={styles.clickId}
                              initial={{ x: -10, opacity: 0 }}
                              animate={{ x: 0, opacity: 1 }}
                              transition={{ delay: index * 0.05 }}
                            >
                              {id}
                            </motion.code>
                          ))
                        ) : (
                          <p className={styles.emptyPrefs}>No clicks yet</p>
                        )}
                      </div>
                    </div>
                  </>
                )}

                {/* Embeddings Tab */}
                {activeTab === 'embeddings' && features.embeddings && (
                  <>
                    <div className={styles.section}>
                      <h4 className={styles.sectionTitle}>User Embeddings (32-dim)</h4>
                      <p className={styles.embeddingDesc}>
                        Showing first 16 dimensions. Hover for values.
                      </p>
                      
                      <EmbeddingViz 
                        embedding={features.embeddings.base_embedding} 
                        label="Base (Batch)" 
                      />
                      <EmbeddingViz 
                        embedding={features.embeddings.delta_embedding} 
                        label="Delta (RT)" 
                      />
                      <EmbeddingViz 
                        embedding={features.embeddings.combined_embedding} 
                        label="Combined" 
                      />
                    </div>

                    <div className={styles.section}>
                      <h4 className={styles.sectionTitle}>Architecture</h4>
                      <div className={styles.architectureInfo}>
                        <div className={styles.archRow}>
                          <span className={styles.archLabel}>Base Weight:</span>
                          <span className={styles.archValue}>60%</span>
                        </div>
                        <div className={styles.archRow}>
                          <span className={styles.archLabel}>Delta Weight:</span>
                          <span className={styles.archValue}>40%</span>
                        </div>
                        <div className={styles.archRow}>
                          <span className={styles.archLabel}>Decay Factor:</span>
                          <span className={styles.archValue}>0.7</span>
                        </div>
                      </div>
                    </div>
                  </>
                )}

                {/* Latency Tab */}
                {activeTab === 'latency' && latencyMetrics && (
                  <div className={styles.section}>
                    <h4 className={styles.sectionTitle}>Pipeline Latency</h4>
                    <div className={styles.latencyBars}>
                      <LatencyBar 
                        label="Feature Serving" 
                        value={latencyMetrics.featureServing} 
                        color="var(--cat-electronics)"
                      />
                      <LatencyBar 
                        label="Embedding Compute" 
                        value={latencyMetrics.embeddingCompute} 
                        color="var(--cat-fashion)"
                      />
                      <LatencyBar 
                        label="Similarity Compute" 
                        value={latencyMetrics.similarityCompute} 
                        color="var(--cat-home)"
                      />
                      <LatencyBar 
                        label="Delta Update" 
                        value={latencyMetrics.deltaUpdate} 
                        color="var(--cat-sports)"
                      />
                      <div className={styles.latencyDivider} />
                      <LatencyBar 
                        label="Total" 
                        value={latencyMetrics.total} 
                        color="var(--accent-primary)"
                        isTotal
                      />
                    </div>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.aside>
  );
}

function LatencyBar({ 
  label, 
  value, 
  color, 
  isTotal = false 
}: { 
  label: string; 
  value: number; 
  color: string;
  isTotal?: boolean;
}) {
  const maxMs = 100; // Scale bar to 100ms max
  const percentage = Math.min((value / maxMs) * 100, 100);
  
  return (
    <div className={`${styles.latencyRow} ${isTotal ? styles.latencyTotal : ''}`}>
      <div className={styles.latencyHeader}>
        <span className={styles.latencyLabel}>{label}</span>
        <span className={styles.latencyValue}>{value.toFixed(1)} ms</span>
      </div>
      <div className={styles.latencyBarTrack}>
        <motion.div
          className={styles.latencyBar}
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}
