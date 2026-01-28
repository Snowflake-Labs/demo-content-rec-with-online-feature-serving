"""
Toggle Online Feature Serving

This script enables or disables Online Feature Serving for the demo.
Use this to manage costs when not actively using the demo.

Usage:
    cd backend

    # Check current status
    uv run python ../scripts/toggle_online_serving.py status

    # Enable Online Serving
    uv run python ../scripts/toggle_online_serving.py enable

    # Disable Online Serving
    uv run python ../scripts/toggle_online_serving.py disable
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from backend/.env
script_dir = Path(__file__).parent
env_path = script_dir.parent / "backend" / ".env"
load_dotenv(env_path)


def get_session():
    """Create Snowflake session."""
    from snowflake.snowpark import Session

    connection_params = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "CONTENT_REC_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "CONTENT_REC_DEMO"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "FEATURES"),
        "role": os.getenv("SNOWFLAKE_ROLE", "CONTENT_REC_ROLE"),
    }

    # Authentication
    snowflake_token = os.getenv("SNOWFLAKE_TOKEN")
    snowflake_password = os.getenv("SNOWFLAKE_PASSWORD")

    if snowflake_token:
        connection_params["token"] = snowflake_token
        connection_params["authenticator"] = "PROGRAMMATIC_ACCESS_TOKEN"
    elif snowflake_password:
        connection_params["password"] = snowflake_password
    else:
        print("Error: No authentication configured. Set SNOWFLAKE_TOKEN or SNOWFLAKE_PASSWORD")
        sys.exit(1)

    return Session.builder.configs(connection_params).create()


def get_feature_store(session):
    """Get Feature Store instance."""
    from snowflake.ml.feature_store import FeatureStore

    return FeatureStore(
        session=session,
        database=os.getenv("SNOWFLAKE_DATABASE", "CONTENT_REC_DEMO"),
        name=os.getenv("SNOWFLAKE_SCHEMA", "FEATURES"),
        default_warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "CONTENT_REC_WH"),
    )


def get_status(session, fs):
    """Check current Online Feature Serving status."""
    print("\n📊 Online Feature Serving Status")
    print("=" * 50)

    try:
        fv_list = fs.list_feature_views().to_pandas()

        if not fv_list.empty:
            row = fv_list[fv_list["NAME"] == "USER_CLICK_FEATURES"].iloc[0]
            online_config = row.get("ONLINE_CONFIG", "{}")
            print("Feature View: USER_CLICK_FEATURES v1")
            print(f"Online Config: {online_config}")

            if '"enable": true' in str(online_config).lower():
                print("\n✅ Status: ENABLED")
                print("   Online Feature Serving is active and incurring costs.")
            else:
                print("\n⏹️  Status: DISABLED")
                print("   Online Feature Serving is stopped. No additional costs.")
        else:
            print("❌ Feature View not found")

    except Exception as e:
        print(f"❌ Error checking status: {e}")


def enable_online_serving(session, fs):
    """Enable Online Feature Serving."""
    from snowflake.ml.feature_store.feature_view import OnlineConfig

    print("\n🚀 Enabling Online Feature Serving...")

    try:
        fs.update_feature_view(
            name="USER_CLICK_FEATURES",
            version="1",
            online_config=OnlineConfig(
                enable=True,
                target_lag="10 seconds",
            ),
        )
        print("✅ Online Feature Serving ENABLED")
        print("   Target lag: 10 seconds")
        print("\n⚠️  Note: This will incur costs while enabled.")

    except Exception as e:
        print(f"❌ Error enabling: {e}")


def disable_online_serving(session, fs):
    """Disable Online Feature Serving."""
    from snowflake.ml.feature_store.feature_view import OnlineConfig

    print("\n⏹️  Disabling Online Feature Serving...")

    try:
        fs.update_feature_view(
            name="USER_CLICK_FEATURES",
            version="1",
            online_config=OnlineConfig(enable=False),
        )
        print("✅ Online Feature Serving DISABLED")
        print("   No additional costs will be incurred.")

    except Exception as e:
        print(f"❌ Error disabling: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Toggle Online Feature Serving for the demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python ../scripts/toggle_online_serving.py status   # Check current status
  uv run python ../scripts/toggle_online_serving.py enable   # Enable (costs apply)
  uv run python ../scripts/toggle_online_serving.py disable  # Disable (save costs)
        """,
    )
    parser.add_argument(
        "action",
        choices=["status", "enable", "disable"],
        help="Action to perform",
    )

    args = parser.parse_args()

    print("Connecting to Snowflake...")
    session = get_session()
    fs = get_feature_store(session)
    print("Connected!")

    if args.action == "status":
        get_status(session, fs)
    elif args.action == "enable":
        enable_online_serving(session, fs)
        get_status(session, fs)
    elif args.action == "disable":
        disable_online_serving(session, fs)
        get_status(session, fs)

    session.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
