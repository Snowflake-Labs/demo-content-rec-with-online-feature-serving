"""
Snowflake Feature Store Setup Script

This script creates the Feature Store entities and Feature Views
with Online Feature Serving enabled using the Python API.

Reference: https://docs.snowflake.com/ja/developer-guide/snowflake-ml/feature-store/create-and-serve-online-features-python

Usage:
    cd backend
    uv run python ../scripts/setup_feature_store.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from backend/.env
# Script is in scripts/, .env is in backend/
script_dir = Path(__file__).parent
env_path = script_dir.parent / "backend" / ".env"
load_dotenv(env_path)

# Debug: Print if token is found
if os.getenv("SNOWFLAKE_TOKEN"):
    print(f"Found SNOWFLAKE_TOKEN in {env_path}")
else:
    print(f"WARNING: SNOWFLAKE_TOKEN not found. Checked: {env_path}")


def setup_feature_store():
    """Set up the Feature Store with online serving enabled."""
    from snowflake.ml.feature_store import CreationMode, Entity, FeatureStore, FeatureView
    from snowflake.ml.feature_store.feature_view import OnlineConfig
    from snowflake.snowpark import Session

    # Connection parameters
    connection_params = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "CONTENT_REC_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "CONTENT_REC_DEMO"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "FEATURES"),
        "role": os.getenv("SNOWFLAKE_ROLE", "PUBLIC"),
    }

    # Authentication: PAT (Programmatic Access Token) or Password
    snowflake_token = os.getenv("SNOWFLAKE_TOKEN")
    snowflake_password = os.getenv("SNOWFLAKE_PASSWORD")

    if snowflake_token:
        # Use PAT authentication
        connection_params["token"] = snowflake_token
        connection_params["authenticator"] = "PROGRAMMATIC_ACCESS_TOKEN"
        print("Using PAT (Programmatic Access Token) authentication")
    elif snowflake_password:
        # Use password authentication
        connection_params["password"] = snowflake_password
        print("Using password authentication")
    else:
        raise ValueError(
            "No authentication method configured. "
            "Set SNOWFLAKE_TOKEN (PAT) or SNOWFLAKE_PASSWORD in .env"
        )

    print("Connecting to Snowflake...")
    session = Session.builder.configs(connection_params).create()
    print(f"Connected! Session: {session}")

    # Create Feature Store
    print("\nCreating Feature Store...")
    fs = FeatureStore(
        session=session,
        database=connection_params["database"],
        name=connection_params["schema"],
        default_warehouse=connection_params["warehouse"],
        creation_mode=CreationMode.CREATE_IF_NOT_EXIST,
    )
    print(f"Feature Store created: {fs}")

    # Create User Entity
    print("\nCreating User Entity...")
    user_entity = Entity(
        name="USER", join_keys=["USER_ID"], desc="User entity for content recommendation"
    )

    try:
        fs.register_entity(user_entity)
        print("User entity registered successfully")
    except Exception as e:
        print(f"Entity may already exist: {e}")

    # Create Feature View with Online Serving
    print("\nCreating Feature View with Online Serving...")

    # Get the source dataframe
    user_features_df = session.table("USER_FEATURES")

    # Create Feature View configuration
    fv = FeatureView(
        name="USER_CLICK_FEATURES",
        entities=[user_entity],
        feature_df=user_features_df,
        refresh_freq="1 minute",  # How often to refresh from source
        desc="User click behavior features for real-time recommendations",
    )

    # Register with online serving enabled
    try:
        registered_fv = fs.register_feature_view(
            feature_view=fv,
            version="1",
            # Enable online serving with 10 second target lag
            # This creates the low-latency serving infrastructure
        )
        print(f"Feature View registered: {registered_fv.name}")

        # Enable online serving
        print("\nEnabling Online Feature Serving...")
        fs.update_feature_view(
            name="USER_CLICK_FEATURES",
            version="1",
            online_config=OnlineConfig(
                enable=True,
                target_lag="10 seconds",  # Target data freshness for online store
            ),
        )
        print("Online Feature Serving enabled with 10 second target lag")

    except Exception as e:
        print(f"Feature View may already exist: {e}")

        # Try to update existing feature view
        print("\nAttempting to update existing Feature View...")
        try:
            fs.update_feature_view(
                name="USER_CLICK_FEATURES",
                version="1",
                online_config=OnlineConfig(enable=True, target_lag="10 seconds"),
            )
            print("Online Feature Serving enabled on existing Feature View")
        except Exception as e2:
            print(f"Update failed: {e2}")

    # Verify setup
    print("\n" + "=" * 50)
    print("Feature Store Setup Complete!")
    print("=" * 50)

    # List registered entities
    print("\nRegistered Entities:")
    entities = fs.list_entities()
    print(entities.to_pandas())

    # List feature views
    print("\nRegistered Feature Views:")
    feature_views = fs.list_feature_views()
    print(feature_views.to_pandas())

    # Test online feature retrieval
    print("\nTesting Online Feature Retrieval...")
    try:
        from snowflake.ml.feature_store import StoreType

        fv = fs.get_feature_view(name="USER_CLICK_FEATURES", version="1")
        result = fs.read_feature_view(
            feature_view=fv,
            keys=[["demo_user"]],
            feature_names=["RECENT_CLICK_IDS", "CATEGORY_PREFERENCE", "TOTAL_CLICKS"],
            store_type=StoreType.ONLINE,
        )
        print("Online Feature Retrieval Test:")
        print(result.to_pandas())
    except Exception as e:
        print(f"Test retrieval failed (user may not exist yet): {e}")

    session.close()
    print("\nSetup complete!")


if __name__ == "__main__":
    setup_feature_store()
