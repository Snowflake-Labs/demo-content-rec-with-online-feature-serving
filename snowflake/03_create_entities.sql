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
-- Step 3: Feature Store Entities
-- ============================================

-- ============================================
-- IMPORTANT: Entity creation requires Python API
-- ============================================
--
-- Snowflake ML Feature Store Entities cannot be created via SQL.
-- Use the Python script instead:
--
--   cd backend
--   uv run python ../scripts/setup_feature_store.py
--
-- The Python script will:
--   1. Create Feature Store
--   2. Register USER entity with join key "USER_ID"
--   3. Create Feature View "USER_CLICK_FEATURES"
--   4. Enable Online Feature Serving with 10 second target lag
--
-- ============================================

-- This file is kept for documentation purposes
-- Switch to the demo role (for verification queries below)
USE ROLE CONTENT_REC_ROLE;
USE DATABASE CONTENT_REC_DEMO;
USE WAREHOUSE CONTENT_REC_WH;
USE SCHEMA FEATURES;

-- ============================================
-- Verification (run after Python script)
-- ============================================

-- Check if USER_FEATURES table exists (created in step 2)
SHOW TABLES LIKE 'USER_FEATURES' IN SCHEMA CONTENT_REC_DEMO.FEATURES;

-- Check current data in USER_FEATURES
SELECT * FROM USER_FEATURES LIMIT 10;

-- Success message
SELECT 
    'Run Python script to create Feature Store entities:' AS STATUS,
    'cd backend && uv run python ../scripts/setup_feature_store.py' AS COMMAND;
