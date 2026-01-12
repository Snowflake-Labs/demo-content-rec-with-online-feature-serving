-- ============================================
-- Snowflake Online Feature Serving Demo
-- Step 3: Create Feature Store Entities
-- ============================================

USE DATABASE CONTENT_REC_DEMO;
USE SCHEMA FEATURES;

-- Create Feature Store (Snowflake ML Feature Store)
-- Note: This requires Snowflake ML Features to be enabled in your account

-- Create the Feature Store entity for users
-- The entity defines the primary key for feature lookups
CREATE OR REPLACE SNOWFLAKE.ML.ENTITY USER_ENTITY(
    user_id STRING
)
COMMENT = 'Entity representing a user for the content recommendation system';

-- Create the Feature Store entity for products (optional, for future expansion)
CREATE OR REPLACE SNOWFLAKE.ML.ENTITY PRODUCT_ENTITY(
    product_id STRING
)
COMMENT = 'Entity representing a product in the catalog';

-- Verify entities were created
SHOW SNOWFLAKE.ML.ENTITIES;

-- Success message
SELECT 'Feature Store entities created successfully!' AS STATUS;
