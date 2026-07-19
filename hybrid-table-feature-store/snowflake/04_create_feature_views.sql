-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
-- http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- ============================================
-- Snowflake Online Feature Serving Demo
-- Step 4: Feature Views for Online Serving
-- ============================================
--
-- ============================================
-- IMPORTANT: Feature Views require Python API
-- ============================================
--
-- Feature Views with Online Serving cannot be created via SQL.
-- Use the Python script instead:
--
--   cd backend
--   uv run python ../scripts/setup_feature_store.py
--
-- Python API example:
--
--   from snowflake.ml.feature_store import FeatureStore, FeatureView, Entity
--   from snowflake.ml.feature_store.feature_view import OnlineConfig
--
--   fs = FeatureStore(session=session, database="CONTENT_REC_DEMO", name="FEATURES")
--
--   # Create entity
--   user_entity = Entity(name="USER", join_keys=["USER_ID"])
--   fs.register_entity(user_entity)
--
--   # Create feature view with online serving enabled
--   fv = FeatureView(
--       name="USER_CLICK_FEATURES",
--       entities=[user_entity],
--       feature_df=session.table("USER_FEATURES"),
--       refresh_freq="1 minute",
--   )
--   fs.register_feature_view(feature_view=fv, version="1")
--
--   # Enable online serving
--   fs.update_feature_view(
--       name="USER_CLICK_FEATURES",
--       version="1",
--       online_config=OnlineConfig(enable=True, target_lag="10 seconds")
--   )
--
-- Reference: https://docs.snowflake.com/ja/developer-guide/snowflake-ml/feature-store/create-and-serve-online-features-python
-- ============================================

-- Switch to the demo role
USE ROLE CONTENT_REC_ROLE;

-- Use the demo database and warehouse
USE DATABASE CONTENT_REC_DEMO;
USE WAREHOUSE CONTENT_REC_WH;
USE SCHEMA FEATURES;

-- ============================================
-- Verification (run after Python script)
-- ============================================

-- Verify USER_FEATURES table exists (source for Feature View)
SHOW TABLES LIKE 'USER_FEATURES' IN SCHEMA CONTENT_REC_DEMO.FEATURES;

-- Check table structure
DESCRIBE TABLE USER_FEATURES;

-- Check current data
SELECT * FROM USER_FEATURES LIMIT 10;

-- Success message
SELECT 
    'Run Python script to create Feature Views:' AS STATUS,
    'cd backend && uv run python ../scripts/setup_feature_store.py' AS COMMAND;
