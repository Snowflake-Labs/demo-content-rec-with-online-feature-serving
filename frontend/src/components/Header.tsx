import { motion } from 'framer-motion';
import styles from './Header.module.css';

interface HeaderProps {
  isUpdating: boolean;
}

export function Header({ isUpdating }: HeaderProps) {
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <div className={styles.logo}>
          <motion.div
            className={styles.logoIcon}
            animate={isUpdating ? { rotate: 360 } : { rotate: 0 }}
            transition={{ duration: 0.5 }}
          >
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <path
                d="M16 2L4 8V24L16 30L28 24V8L16 2Z"
                fill="url(#logo-gradient)"
                stroke="currentColor"
                strokeWidth="1.5"
              />
              <path
                d="M16 12L10 15V21L16 24L22 21V15L16 12Z"
                fill="var(--bg-primary)"
                stroke="currentColor"
                strokeWidth="1"
              />
              <defs>
                <linearGradient id="logo-gradient" x1="4" y1="2" x2="28" y2="30">
                  <stop stopColor="var(--accent-primary)" />
                  <stop offset="1" stopColor="var(--accent-secondary)" />
                </linearGradient>
              </defs>
            </svg>
          </motion.div>
          <span className={styles.logoText}>
            Shop<span className="gradient-text">Smart</span>
          </span>
        </div>

        <div className={styles.tagline}>
          <span className={styles.badge}>
            <span className={styles.badgeDot} />
            Snowflake Online Feature Serving
          </span>
          <span className={styles.subtitle}>Real-time AI Recommendations</span>
        </div>

        <div className={styles.actions}>
          {isUpdating && (
            <motion.div
              className={styles.updateIndicator}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
            >
              <div className={styles.spinner} />
              <span>Updating Features...</span>
            </motion.div>
          )}
        </div>
      </div>
    </header>
  );
}
