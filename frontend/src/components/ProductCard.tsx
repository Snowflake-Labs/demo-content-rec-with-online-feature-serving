import { motion } from 'framer-motion';
import type { Product } from '../api/types';
import styles from './ProductCard.module.css';

interface ProductCardProps {
  product: Product;
  onClick: () => void;
  isRecentlyClicked?: boolean;
  animationDelay?: number;
}

const categoryColors: Record<string, string> = {
  Electronics: 'var(--cat-electronics)',
  Fashion: 'var(--cat-fashion)',
  Home: 'var(--cat-home)',
  Sports: 'var(--cat-sports)',
  Books: 'var(--cat-books)',
};

export function ProductCard({
  product,
  onClick,
  isRecentlyClicked = false,
  animationDelay = 0,
}: ProductCardProps) {
  const categoryColor = categoryColors[product.category] || 'var(--accent-primary)';

  return (
    <motion.article
      className={`${styles.card} ${isRecentlyClicked ? styles.recentlyClicked : ''}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: animationDelay }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      onClick={onClick}
      style={{ '--category-color': categoryColor } as React.CSSProperties}
    >
      <div className={styles.imageContainer}>
        <img
          src={product.image_url || `https://picsum.photos/seed/${product.product_id}/400/400`}
          alt={product.name}
          className={styles.image}
          loading="lazy"
        />
        <div className={styles.categoryBadge}>
          {product.category}
        </div>
        {isRecentlyClicked && (
          <div className={styles.clickedBadge}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M10 3L4.5 8.5L2 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Clicked
          </div>
        )}
      </div>
      
      <div className={styles.content}>
        <h3 className={styles.name}>{product.name}</h3>
        
        <div className={styles.rating}>
          <div className={styles.stars}>
            {[1, 2, 3, 4, 5].map((star) => (
              <svg
                key={star}
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill={star <= Math.round(product.rating) ? 'currentColor' : 'none'}
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <path d="M7 1L8.76 4.56L12.76 5.12L9.88 7.94L10.52 11.94L7 10.12L3.48 11.94L4.12 7.94L1.24 5.12L5.24 4.56L7 1Z" />
              </svg>
            ))}
          </div>
          <span className={styles.reviewCount}>({product.review_count.toLocaleString()})</span>
        </div>
        
        <div className={styles.footer}>
          <span className={styles.price}>${product.price.toFixed(2)}</span>
          <button className={styles.viewButton}>
            View Details
          </button>
        </div>
      </div>
    </motion.article>
  );
}
