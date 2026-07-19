"""
Script 01: Set up a Postgres-backed online feature view for user features.

Differences from the base demo's setup_feature_store.py:
- Uses OnlineStoreType.POSTGRES instead of the default Snowflake online store
- Flattens DELTA_EMBEDDING (ARRAY) into 32 individual FLOAT columns so the
  feature view schema can be used as direct model inputs
- The resulting feature view is what gets passed to
  `create_service(feature_sources_per_function=...)` in script 03

Prerequisites:
  1. A Snowflake Postgres instance must exist.
     Create one in Snowsight: Admin → Postgres → New Instance, or run:
       CREATE SNOWFLAKE POSTGRES INSTANCE content_rec_pg;
  2. USER_FEATURES table populated (run snowflake/ SQL scripts + 05_sample_data.sql)
  3. backend/.env configured with SNOWFLAKE_* credentials

Run from the repo root:
    cd backend && uv run python ../online-feature-store-integration/scripts/01_setup_postgres_feature_view.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Load credentials from existing backend/.env
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / "backend" / ".env")

from snowflake.snowpark import Session
from snowflake.ml.feature_store import (
    CreationMode,
    Entity,
    FeatureStore,
    FeatureView,
    OnlineConfig,
    OnlineStoreType,
)

DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "CONTENT_REC_DEMO")
FS_SCHEMA = "FEATURES"


def _build_session() -> Session:
    params: dict = dict(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "CONTENT_REC_WH"),
        database=DATABASE,
        schema=FS_SCHEMA,
        role=os.environ.get("SNOWFLAKE_ROLE", "PUBLIC"),
    )
    token = os.environ.get("SNOWFLAKE_TOKEN", "")
    password = os.environ.get("SNOWFLAKE_PASSWORD", "")
    if token:
        params.update(authenticator="oauth", token=token)
    elif password:
        params["password"] = password
    else:
        raise ValueError("Set SNOWFLAKE_TOKEN or SNOWFLAKE_PASSWORD in backend/.env")
    return Session.builder.configs(params).create()


def main() -> None:
    session = _build_session()
    print(f"Connected: {session.get_current_account()} / {session.get_current_database()}")

    fs = FeatureStore(
        session=session,
        database=DATABASE,
        name=FS_SCHEMA,
        creation_mode=CreationMode.CREATE_IF_NOT_EXIST,
    )

    user_entity = Entity(name="USER", join_keys=["USER_ID"])
    fs.register_entity(user_entity)
    print("Entity USER registered (or already exists)")

    # Flatten DELTA_EMBEDDING ARRAY[FLOAT] → DELTA_0 .. DELTA_31 so every
    # feature column is a plain scalar that the model can consume directly.
    delta_cols = "\n            ".join(
        f"DELTA_EMBEDDING[{i}]::FLOAT AS DELTA_{i}," for i in range(32)
    ).rstrip(",")

    feature_df = session.sql(f"""
        SELECT
            USER_ID,
            CATEGORY_ELECTRONICS,
            CATEGORY_FASHION,
            CATEGORY_HOME,
            CATEGORY_SPORTS,
            CATEGORY_BOOKS,
            TOTAL_CLICKS,
            LAST_UPDATED,
            {delta_cols}
        FROM USER_FEATURES
    """)

    fv = FeatureView(
        name="USER_FEATURES_ONLINE",
        entities=[user_entity],
        feature_df=feature_df,
        timestamp_col="LAST_UPDATED",
        refresh_freq="1m",
        online_config=OnlineConfig(
            enable=True,
            target_lag="10s",
            store_type=OnlineStoreType.POSTGRES,
        ),
        desc="User profile features for real-time inference via Postgres online store",
    )

    registered_fv = fs.register_feature_view(fv, version="V1", overwrite=True)
    print(f"Registered feature view: {registered_fv.name} / {registered_fv.version}")
    cols = [f.name for f in registered_fv.feature_df.schema]
    print(f"Columns ({len(cols)}): {cols}")


if __name__ == "__main__":
    main()
