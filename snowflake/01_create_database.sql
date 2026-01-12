-- ============================================
-- Snowflake Online Feature Serving Demo
-- Step 1: Create Database, Schema, and Role
-- ============================================

-- ============================================
-- Required Roles:
--   SECURITYADMIN - to create roles and grant permissions
--   SYSADMIN      - to create database, schema, warehouse
--   ACCOUNTADMIN  - for Snowflake ML Feature Store permissions (if needed)
-- ============================================

-- ============================================
-- 1. Create dedicated role for this demo
-- ============================================

-- Switch to SECURITYADMIN to create roles
USE ROLE SECURITYADMIN;

-- Create the demo role
CREATE ROLE IF NOT EXISTS CONTENT_REC_ROLE
    COMMENT = 'Role for Content Recommendation Demo with Online Feature Serving';

-- Grant role to SYSADMIN for administration
GRANT ROLE CONTENT_REC_ROLE TO ROLE SYSADMIN;

-- ============================================
-- 2. Create database and schemas
-- ============================================

-- Switch to SYSADMIN to create database and schemas
USE ROLE SYSADMIN;

-- Create the demo database
CREATE DATABASE IF NOT EXISTS CONTENT_REC_DEMO;

-- Use the database
USE DATABASE CONTENT_REC_DEMO;

-- Create schema for raw data (products, click events)
CREATE SCHEMA IF NOT EXISTS RAW_DATA
    COMMENT = 'Raw data for products and user interactions';

-- Create schema for features (feature store)
CREATE SCHEMA IF NOT EXISTS FEATURES
    COMMENT = 'Feature Store for user and item features';

-- Create schema for ML models
CREATE SCHEMA IF NOT EXISTS ML
    COMMENT = 'ML models and embeddings';

-- ============================================
-- 3. Create warehouse
-- ============================================

-- Create warehouse for the demo (still as SYSADMIN)
CREATE WAREHOUSE IF NOT EXISTS CONTENT_REC_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 15
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for Content Recommendation Demo';

-- ============================================
-- 4. Grant permissions to CONTENT_REC_ROLE
-- ============================================

-- Switch to SECURITYADMIN for granting permissions
USE ROLE SECURITYADMIN;

-- Database permissions
GRANT USAGE ON DATABASE CONTENT_REC_DEMO TO ROLE CONTENT_REC_ROLE;
GRANT CREATE SCHEMA ON DATABASE CONTENT_REC_DEMO TO ROLE CONTENT_REC_ROLE;

-- Schema permissions - RAW_DATA
GRANT USAGE ON SCHEMA CONTENT_REC_DEMO.RAW_DATA TO ROLE CONTENT_REC_ROLE;
GRANT CREATE TABLE ON SCHEMA CONTENT_REC_DEMO.RAW_DATA TO ROLE CONTENT_REC_ROLE;
GRANT CREATE VIEW ON SCHEMA CONTENT_REC_DEMO.RAW_DATA TO ROLE CONTENT_REC_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA CONTENT_REC_DEMO.RAW_DATA TO ROLE CONTENT_REC_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA CONTENT_REC_DEMO.RAW_DATA TO ROLE CONTENT_REC_ROLE;

-- Schema permissions - FEATURES
GRANT USAGE ON SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE CONTENT_REC_ROLE;
GRANT CREATE TABLE ON SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE CONTENT_REC_ROLE;
GRANT CREATE VIEW ON SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE CONTENT_REC_ROLE;
GRANT CREATE DYNAMIC TABLE ON SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE CONTENT_REC_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE CONTENT_REC_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE CONTENT_REC_ROLE;

-- Schema permissions - ML
GRANT USAGE ON SCHEMA CONTENT_REC_DEMO.ML TO ROLE CONTENT_REC_ROLE;
GRANT CREATE TABLE ON SCHEMA CONTENT_REC_DEMO.ML TO ROLE CONTENT_REC_ROLE;
GRANT CREATE VIEW ON SCHEMA CONTENT_REC_DEMO.ML TO ROLE CONTENT_REC_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA CONTENT_REC_DEMO.ML TO ROLE CONTENT_REC_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA CONTENT_REC_DEMO.ML TO ROLE CONTENT_REC_ROLE;

-- Warehouse permissions
GRANT USAGE ON WAREHOUSE CONTENT_REC_WH TO ROLE CONTENT_REC_ROLE;
GRANT OPERATE ON WAREHOUSE CONTENT_REC_WH TO ROLE CONTENT_REC_ROLE;

-- ============================================
-- 5. Grant Snowflake ML Feature Store permissions
-- ============================================

-- Switch to ACCOUNTADMIN for ML permissions
USE ROLE ACCOUNTADMIN;

-- Grant SNOWFLAKE database access for ML features
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CONTENT_REC_ROLE;

-- Grant CREATE privileges for Feature Store objects
-- Feature Store uses Dynamic Tables, Streams, Tasks, and Tags internally
GRANT CREATE DYNAMIC TABLE ON SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE CONTENT_REC_ROLE;
GRANT CREATE STREAM ON SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE CONTENT_REC_ROLE;
GRANT CREATE TASK ON SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE CONTENT_REC_ROLE;
GRANT CREATE PROCEDURE ON SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE CONTENT_REC_ROLE;
GRANT CREATE TAG ON SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE CONTENT_REC_ROLE;

-- Full privileges on FEATURES schema for Feature Store operations
GRANT ALL PRIVILEGES ON SCHEMA CONTENT_REC_DEMO.FEATURES TO ROLE CONTENT_REC_ROLE;

-- Grant EXECUTE TASK for scheduled feature updates
GRANT EXECUTE TASK ON ACCOUNT TO ROLE CONTENT_REC_ROLE;

-- ============================================
-- 6. Grant role to current user
-- ============================================

-- Switch back to SECURITYADMIN
USE ROLE SECURITYADMIN;

-- Show current user (for verification)
SELECT CURRENT_USER() AS CURRENT_USERNAME;

-- Grant CONTENT_REC_ROLE to the current user
-- Using a stored procedure to dynamically grant to current user
DECLARE
    current_username STRING;
BEGIN
    current_username := CURRENT_USER();
    EXECUTE IMMEDIATE 'GRANT ROLE CONTENT_REC_ROLE TO USER ' || :current_username;
    RETURN 'Role CONTENT_REC_ROLE granted to user: ' || :current_username;
END;

-- ============================================
-- Verification
-- ============================================

-- Show created objects
SHOW ROLES LIKE 'CONTENT_REC_ROLE';
SHOW DATABASES LIKE 'CONTENT_REC_DEMO';
SHOW SCHEMAS IN DATABASE CONTENT_REC_DEMO;
SHOW WAREHOUSES LIKE 'CONTENT_REC_WH';

-- Show roles granted to current user (run separately if needed)
-- SHOW GRANTS TO USER <YOUR_USERNAME>;

-- Success message
SELECT 
    'Setup completed successfully!' AS STATUS,
    CURRENT_USER() AS GRANTED_TO_USER,
    'CONTENT_REC_ROLE' AS ROLE_GRANTED;
