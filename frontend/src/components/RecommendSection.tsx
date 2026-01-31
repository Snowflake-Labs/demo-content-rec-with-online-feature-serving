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

import { motion, AnimatePresence } from 'framer-motion';
import type { Product, ScoredProduct } from '../api/types';
import { ProductCard } from './ProductCard';
import styles from './RecommendSection.module.css';

interface RecommendSectionProps {
  recommendations: Product[];
  scoredRecommendations?: ScoredProduct[];
  featureLatency: number;
  totalLatency: number;
  onProductClick: (productId: string) => void;
  isLoading: boolean;
}

export function RecommendSection({
  recommendations,
  scoredRecommendations = [],
  featureLatency,
  totalLatency,
  onProductClick,
  isLoading,
}: RecommendSectionProps) {
  // Create a map of product_id to score info
  const scoreMap = new Map(
    scoredRecommendations.map(sr => [sr.product.product_id, sr])
  );

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <div className={styles.titleRow}>
            <h2 className={styles.title}>
              <span className="gradient-text">Recommended</span> For You
            </h2>
            <div className={styles.aiTag}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path
                  d="M8 1L10 5L14 5.5L11 8.5L12 12.5L8 10.5L4 12.5L5 8.5L2 5.5L6 5L8 1Z"
                  fill="currentColor"
                />
              </svg>
              Two-Tower
            </div>
          </div>
          <p className={styles.subtitle}>
            Ranked by cosine similarity with your embedding
          </p>
        </div>

        <div className={styles.metrics}>
          <div className={styles.metric}>
            <span className={styles.metricLabel}>Feature Serving</span>
            <span className={styles.metricValue}>{featureLatency.toFixed(1)} ms</span>
          </div>
          <div className={styles.metricDivider} />
          <div className={styles.metric}>
            <span className={styles.metricLabel}>Total Response</span>
            <span className={styles.metricValue}>{totalLatency.toFixed(1)} ms</span>
          </div>
        </div>
      </div>

      <div className={styles.content}>
        {isLoading ? (
          <div className={styles.loadingGrid}>
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className={styles.skeleton} />
            ))}
          </div>
        ) : recommendations.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                <path
                  d="M24 4L28 16L40 17L31 26L34 38L24 32L14 38L17 26L8 17L20 16L24 4Z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <h3>No recommendations yet</h3>
            <p>Click on some products above to get personalized recommendations</p>
          </div>
        ) : (
          <motion.div layout className={styles.grid}>
            <AnimatePresence mode="popLayout">
              {recommendations.map((product, index) => {
                const scoreInfo = scoreMap.get(product.product_id);
                const similarity = scoreInfo?.score_breakdown?.cosine_similarity ?? 0;
                
                return (
                  <motion.div
                    key={product.product_id}
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                    className={styles.cardWrapper}
                  >
                    <ProductCard
                      product={product}
                      onClick={() => onProductClick(product.product_id)}
                    />
                    {scoreInfo && (
                      <div className={styles.scoreOverlay}>
                        <div className={styles.scoreRank}>#{index + 1}</div>
                        <div className={styles.scoreValue}>
                          {(similarity * 100).toFixed(0)}% match
                        </div>
                      </div>
                    )}
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </motion.div>
        )}
      </div>
    </section>
  );
}
