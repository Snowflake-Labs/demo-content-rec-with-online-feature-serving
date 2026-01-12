-- ============================================
-- Snowflake Online Feature Serving Demo
-- Step 4: Create Feature Views for Online Serving
-- ============================================
-- 
-- NOTE: This SQL script creates the underlying tables.
-- The Feature View with Online Serving should be created using Python API:
--
-- from snowflake.ml.feature_store import FeatureStore, FeatureView, Entity
-- from snowflake.ml.feature_store.feature_view import OnlineConfig
--
-- fs = FeatureStore(session=session, database="CONTENT_REC_DEMO", name="FEATURES")
-- 
-- # Create entity
-- user_entity = Entity(name="USER", join_keys=["USER_ID"])
-- fs.register_entity(user_entity)
--
-- # Create feature view with online serving enabled
-- fv = FeatureView(
--     name="USER_CLICK_FEATURES",
--     entities=[user_entity],
--     feature_df=session.table("USER_FEATURES"),
--     refresh_freq="1 minute",
--     online_config=OnlineConfig(enable=True, target_lag="10 seconds")
-- )
-- fs.register_feature_view(feature_view=fv, version="1")
--
-- Reference: https://docs.snowflake.com/ja/developer-guide/snowflake-ml/feature-store/create-and-serve-online-features-python
-- ============================================

USE DATABASE CONTENT_REC_DEMO;
USE SCHEMA FEATURES;

-- Ensure the USER_FEATURES table exists (created in 02_create_feature_store.sql)
-- This table will be the source for the Feature View

-- Alternative: If using SQL-based Feature View (legacy approach)
-- This creates a Dynamic Table that can be used with Feature Store

-- CREATE OR REPLACE DYNAMIC TABLE USER_CLICK_FEATURES_DT
--     TARGET_LAG = '1 minute'
--     WAREHOUSE = CONTENT_REC_WH
--     AS
--     SELECT
--         user_id,
--         recent_click_ids,
--         category_preference,
--         total_clicks,
--         last_click_timestamp,
--         updated_at
--     FROM USER_FEATURES;

-- Verify tables exist
SELECT 'USER_FEATURES table ready for Feature View' AS STATUS
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME = 'USER_FEATURES' AND TABLE_SCHEMA = 'FEATURES';
