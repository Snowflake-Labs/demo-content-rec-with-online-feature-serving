-- ============================================
-- Snowflake Online Feature Serving Demo
-- Step 2: Create Feature Store Components
-- ============================================

-- ============================================
-- Prerequisites:
--   Run 01_create_database.sql first
--   This script uses CONTENT_REC_ROLE
-- ============================================

-- Switch to the demo role
USE ROLE CONTENT_REC_ROLE;

-- Use the demo database and warehouse
USE DATABASE CONTENT_REC_DEMO;
USE WAREHOUSE CONTENT_REC_WH;
USE SCHEMA FEATURES;

-- ============================================
-- 1. Create click events source table
-- ============================================

-- This table stores raw click events from the web application
CREATE TABLE IF NOT EXISTS CLICK_EVENTS (
    event_id STRING DEFAULT UUID_STRING(),
    user_id STRING NOT NULL,
    product_id STRING NOT NULL,
    category STRING NOT NULL,
    clicked_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (event_id)
);

-- ============================================
-- 2. Create user features table
-- ============================================

-- This table stores aggregated user features for recommendations
CREATE OR REPLACE TABLE USER_FEATURES (
    user_id STRING NOT NULL PRIMARY KEY,
    recent_click_ids ARRAY,           -- Last 10 clicked product IDs
    category_preference OBJECT,        -- Map of category -> click count
    total_clicks INTEGER DEFAULT 0,
    last_click_timestamp TIMESTAMP_NTZ,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================
-- 3. Create stream for change tracking
-- ============================================

-- Create a stream on click events to track changes (for batch processing if needed)
CREATE OR REPLACE STREAM CLICK_EVENTS_STREAM ON TABLE CLICK_EVENTS
    APPEND_ONLY = TRUE;

-- ============================================
-- 4. Create stored procedure for feature updates
-- ============================================

-- This procedure updates user features when a click occurs
CREATE OR REPLACE PROCEDURE UPDATE_USER_FEATURES(
    p_user_id STRING,
    p_product_id STRING,
    p_category STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    current_clicks ARRAY;
    current_prefs OBJECT;
    current_count INTEGER;
    new_clicks ARRAY;
    new_prefs OBJECT;
    category_count INTEGER;
BEGIN
    -- Get current user features
    SELECT recent_click_ids, category_preference, total_clicks
    INTO :current_clicks, :current_prefs, :current_count
    FROM USER_FEATURES
    WHERE user_id = :p_user_id;

    -- If user doesn't exist, initialize
    IF (current_clicks IS NULL) THEN
        current_clicks := ARRAY_CONSTRUCT();
        current_prefs := OBJECT_CONSTRUCT();
        current_count := 0;
    END IF;

    -- Update recent clicks (keep last 10)
    new_clicks := ARRAY_PREPEND(:current_clicks, :p_product_id);
    IF (ARRAY_SIZE(:new_clicks) > 10) THEN
        new_clicks := ARRAY_SLICE(:new_clicks, 0, 10);
    END IF;

    -- Update category preference
    category_count := COALESCE(current_prefs[:p_category]::INTEGER, 0) + 1;
    new_prefs := OBJECT_INSERT(:current_prefs, :p_category, :category_count, TRUE);

    -- Upsert user features
    MERGE INTO USER_FEATURES AS target
    USING (SELECT :p_user_id AS user_id) AS source
    ON target.user_id = source.user_id
    WHEN MATCHED THEN
        UPDATE SET
            recent_click_ids = :new_clicks,
            category_preference = :new_prefs,
            total_clicks = :current_count + 1,
            last_click_timestamp = CURRENT_TIMESTAMP(),
            updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (user_id, recent_click_ids, category_preference, total_clicks, last_click_timestamp)
        VALUES (:p_user_id, :new_clicks, :new_prefs, 1, CURRENT_TIMESTAMP());

    RETURN 'SUCCESS';
END;
$$;

-- ============================================
-- Verification
-- ============================================

-- Show created objects
SHOW TABLES IN SCHEMA CONTENT_REC_DEMO.FEATURES;
SHOW STREAMS IN SCHEMA CONTENT_REC_DEMO.FEATURES;
SHOW PROCEDURES IN SCHEMA CONTENT_REC_DEMO.FEATURES;

-- Success message
SELECT 
    'Feature Store components created successfully!' AS STATUS,
    CURRENT_ROLE() AS ROLE_USED,
    CURRENT_DATABASE() AS DATABASE_USED,
    CURRENT_SCHEMA() AS SCHEMA_USED;
