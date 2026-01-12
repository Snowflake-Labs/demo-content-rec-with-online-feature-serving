import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Product } from '../api/types';
import { ProductCard } from './ProductCard';
import styles from './ProductGrid.module.css';

interface ProductGridProps {
  products: Product[];
  recentClickIds: string[];
  onProductClick: (productId: string) => void;
}

const CATEGORIES = ['All', 'Electronics', 'Fashion', 'Home', 'Sports', 'Books'];

export function ProductGrid({
  products,
  recentClickIds,
  onProductClick,
}: ProductGridProps) {
  const [selectedCategory, setSelectedCategory] = useState('All');

  const filteredProducts =
    selectedCategory === 'All'
      ? products
      : products.filter((p) => p.category === selectedCategory);

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <h2 className={styles.title}>Browse Products</h2>
          <p className={styles.subtitle}>
            Click on products to update your preferences in real-time
          </p>
        </div>

        <div className={styles.filters}>
          {CATEGORIES.map((category) => (
            <button
              key={category}
              className={`${styles.filterButton} ${
                selectedCategory === category ? styles.active : ''
              }`}
              onClick={() => setSelectedCategory(category)}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      <motion.div layout className={styles.grid}>
        <AnimatePresence mode="popLayout">
          {filteredProducts.map((product, index) => (
            <ProductCard
              key={product.product_id}
              product={product}
              onClick={() => onProductClick(product.product_id)}
              isRecentlyClicked={recentClickIds.includes(product.product_id)}
              animationDelay={index * 0.05}
            />
          ))}
        </AnimatePresence>
      </motion.div>
    </section>
  );
}
