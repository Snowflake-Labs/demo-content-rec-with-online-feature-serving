-- ============================================
-- Snowflake Online Feature Serving Demo
-- Step 5: Insert Sample Product and User Data
-- ============================================

-- Switch to the demo role
USE ROLE CONTENT_REC_ROLE;

-- Use the demo database and warehouse
USE DATABASE CONTENT_REC_DEMO;
USE WAREHOUSE CONTENT_REC_WH;
USE SCHEMA RAW_DATA;

-- Create Products table
CREATE TABLE IF NOT EXISTS PRODUCTS (
    product_id STRING NOT NULL PRIMARY KEY,
    name STRING NOT NULL,
    category STRING NOT NULL,
    description STRING,
    price DECIMAL(10, 2),
    image_url STRING,
    rating DECIMAL(2, 1) DEFAULT 4.0,
    review_count INTEGER DEFAULT 0,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Insert sample products across different categories
INSERT INTO PRODUCTS (product_id, name, category, description, price, image_url, rating, review_count)
VALUES
    -- Electronics
    ('PROD001', 'Wireless Bluetooth Headphones', 'Electronics', 'Premium noise-canceling headphones with 30-hour battery life', 299.99, 'https://picsum.photos/seed/headphones/400/400', 4.5, 1250),
    ('PROD002', '4K Ultra HD Smart TV 55"', 'Electronics', 'Crystal clear display with smart home integration', 799.99, 'https://picsum.photos/seed/tv/400/400', 4.7, 890),
    ('PROD003', 'Portable Bluetooth Speaker', 'Electronics', 'Waterproof speaker with 360-degree sound', 149.99, 'https://picsum.photos/seed/speaker/400/400', 4.3, 2100),
    ('PROD004', 'Wireless Gaming Mouse', 'Electronics', 'Ultra-fast response time with RGB lighting', 79.99, 'https://picsum.photos/seed/mouse/400/400', 4.6, 3200),
    ('PROD005', 'Smart Watch Pro', 'Electronics', 'Health tracking with GPS and cellular', 449.99, 'https://picsum.photos/seed/watch/400/400', 4.4, 1800),
    -- Fashion
    ('PROD006', 'Premium Leather Jacket', 'Fashion', 'Genuine leather with modern slim fit', 399.99, 'https://picsum.photos/seed/jacket/400/400', 4.8, 560),
    ('PROD007', 'Classic Denim Jeans', 'Fashion', 'Comfortable stretch denim with perfect fit', 89.99, 'https://picsum.photos/seed/jeans/400/400', 4.2, 4500),
    ('PROD008', 'Running Sneakers', 'Fashion', 'Lightweight with responsive cushioning', 129.99, 'https://picsum.photos/seed/sneakers/400/400', 4.5, 2800),
    ('PROD009', 'Wool Blend Sweater', 'Fashion', 'Warm and stylish for all occasions', 79.99, 'https://picsum.photos/seed/sweater/400/400', 4.3, 1200),
    ('PROD010', 'Designer Sunglasses', 'Fashion', 'UV protection with polarized lenses', 199.99, 'https://picsum.photos/seed/sunglasses/400/400', 4.6, 980),
    -- Home & Kitchen
    ('PROD011', 'Espresso Coffee Machine', 'Home', 'Professional-grade with built-in grinder', 599.99, 'https://picsum.photos/seed/coffee/400/400', 4.7, 750),
    ('PROD012', 'Air Fryer XL', 'Home', 'Healthy cooking with rapid air technology', 159.99, 'https://picsum.photos/seed/airfryer/400/400', 4.4, 5600),
    ('PROD013', 'Robot Vacuum Cleaner', 'Home', 'Smart navigation with app control', 449.99, 'https://picsum.photos/seed/vacuum/400/400', 4.3, 2100),
    ('PROD014', 'Memory Foam Pillow Set', 'Home', 'Ergonomic design for better sleep', 69.99, 'https://picsum.photos/seed/pillow/400/400', 4.5, 8900),
    ('PROD015', 'Stainless Steel Cookware Set', 'Home', '10-piece professional grade set', 299.99, 'https://picsum.photos/seed/cookware/400/400', 4.6, 1450),
    -- Sports & Outdoors
    ('PROD016', 'Yoga Mat Premium', 'Sports', 'Extra thick with non-slip surface', 49.99, 'https://picsum.photos/seed/yoga/400/400', 4.7, 6700),
    ('PROD017', 'Adjustable Dumbbell Set', 'Sports', 'Space-saving design 5-50 lbs', 349.99, 'https://picsum.photos/seed/dumbbell/400/400', 4.5, 1890),
    ('PROD018', 'Camping Tent 4-Person', 'Sports', 'Weatherproof with easy setup', 199.99, 'https://picsum.photos/seed/tent/400/400', 4.4, 920),
    ('PROD019', 'Mountain Bike Helmet', 'Sports', 'Lightweight with ventilation system', 89.99, 'https://picsum.photos/seed/helmet/400/400', 4.6, 2300),
    ('PROD020', 'Fitness Tracker Band', 'Sports', 'Heart rate and sleep monitoring', 79.99, 'https://picsum.photos/seed/tracker/400/400', 4.2, 4100),
    -- Books & Media
    ('PROD021', 'Bestseller Novel Collection', 'Books', 'Top 5 fiction books of the year', 59.99, 'https://picsum.photos/seed/books/400/400', 4.8, 3400),
    ('PROD022', 'Programming Guide Bundle', 'Books', 'Complete guide to modern development', 89.99, 'https://picsum.photos/seed/coding/400/400', 4.5, 1200),
    ('PROD023', 'Cookbook: World Cuisines', 'Books', '500+ recipes from around the globe', 39.99, 'https://picsum.photos/seed/cookbook/400/400', 4.6, 2800),
    ('PROD024', 'Photography Art Book', 'Books', 'Stunning collection of nature photography', 49.99, 'https://picsum.photos/seed/artbook/400/400', 4.7, 890),
    ('PROD025', 'Business Strategy Guide', 'Books', 'Leadership and management essentials', 34.99, 'https://picsum.photos/seed/business/400/400', 4.3, 1560);

-- Initialize some sample users with features
USE SCHEMA FEATURES;

-- Insert sample users with pre-existing preferences
-- Using INSERT ... SELECT because ARRAY_CONSTRUCT/OBJECT_CONSTRUCT cannot be used in VALUES clause

INSERT INTO USER_FEATURES (user_id, recent_click_ids, category_preference, total_clicks, last_click_timestamp)
SELECT 
    'user_demo_001',
    ARRAY_CONSTRUCT('PROD001', 'PROD002', 'PROD003'),
    OBJECT_CONSTRUCT('Electronics', 3),
    3,
    CURRENT_TIMESTAMP();

INSERT INTO USER_FEATURES (user_id, recent_click_ids, category_preference, total_clicks, last_click_timestamp)
SELECT 
    'user_demo_002',
    ARRAY_CONSTRUCT('PROD006', 'PROD008', 'PROD007', 'PROD010'),
    OBJECT_CONSTRUCT('Fashion', 4),
    4,
    CURRENT_TIMESTAMP();

INSERT INTO USER_FEATURES (user_id, recent_click_ids, category_preference, total_clicks, last_click_timestamp)
SELECT 
    'user_demo_003',
    ARRAY_CONSTRUCT('PROD016', 'PROD017', 'PROD011'),
    OBJECT_CONSTRUCT('Sports', 2, 'Home', 1),
    3,
    CURRENT_TIMESTAMP();

-- Verify data
SELECT 'Products inserted: ' || COUNT(*) AS STATUS FROM RAW_DATA.PRODUCTS;
SELECT 'Users initialized: ' || COUNT(*) AS STATUS FROM FEATURES.USER_FEATURES;

-- Success message
SELECT 'Sample data inserted successfully!' AS STATUS;
