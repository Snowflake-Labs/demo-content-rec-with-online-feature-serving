-- ============================================
-- Snowflake Online Feature Serving Demo
-- Step 1: Create Database and Schema
-- ============================================

-- Create the demo database
CREATE DATABASE IF NOT EXISTS CONTENT_REC_DEMO;

-- Use the database
USE DATABASE CONTENT_REC_DEMO;

-- Create schema for raw data
CREATE SCHEMA IF NOT EXISTS RAW_DATA;

-- Create schema for features
CREATE SCHEMA IF NOT EXISTS FEATURES;

-- Create schema for ML models (if needed)
CREATE SCHEMA IF NOT EXISTS ML;

-- Grant usage permissions (adjust roles as needed)
GRANT USAGE ON DATABASE CONTENT_REC_DEMO TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA CONTENT_REC_DEMO.RAW_DATA TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE PUBLIC;

-- Create warehouse for the demo (if not exists)
CREATE WAREHOUSE IF NOT EXISTS CONTENT_REC_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

GRANT USAGE ON WAREHOUSE CONTENT_REC_WH TO ROLE PUBLIC;

-- Success message
SELECT 'Database and schemas created successfully!' AS STATUS;
