"""
Script 03: Deploy UserEmbeddingModel as a REST inference service with
automatic Online Feature Store lookup.

Key difference from a standard create_service() call:

    mv.create_service(
        ...
        feature_sources_per_function={"predict": [user_fv]},  # <— this
    )

At inference time the service will:
  1. Receive a request containing only USER_ID
  2. Look up the full feature row from the Postgres-backed online store
  3. Pass all feature columns to predict()
  4. Return the 32-dim user embedding

Prerequisites:
  - Script 01 completed (Postgres-backed feature view registered)
  - Script 02 completed (model logged to registry)
  - A compute pool exists (or use SYSTEM_COMPUTE_POOL_CPU)

Run from the repo root:
    cd backend && uv run python ../online-feature-store-integration/scripts/03_deploy_with_feature_integration.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / "backend" / ".env")

from snowflake.ml.feature_store import CreationMode, FeatureStore
from snowflake.ml.registry import Registry
from snowflake.snowpark import Session

DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "CONTENT_REC_DEMO")
FS_SCHEMA = "FEATURES"
MODELS_SCHEMA = "MODELS"
MODEL_NAME = "USER_EMBEDDING_MODEL"
MODEL_VERSION = "V1"
SERVICE_NAME = "USER_EMBEDDING_SERVICE"
# Use the system CPU compute pool to avoid needing a dedicated pool.
# Swap for a named pool if you need a specific instance type.
COMPUTE_POOL = os.environ.get("SNOWFLAKE_COMPUTE_POOL", "SYSTEM_COMPUTE_POOL_CPU")


def _build_session() -> Session:
    params: dict = dict(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "CONTENT_REC_WH"),
        database=DATABASE,
        schema=MODELS_SCHEMA,
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
    print(f"Connected: {session.get_current_account()}")

    # Retrieve the registered Postgres-backed feature view
    fs = FeatureStore(
        session=session,
        database=DATABASE,
        name=FS_SCHEMA,
        creation_mode=CreationMode.FAIL_IF_NOT_EXIST,
    )
    user_fv = fs.get_feature_view("USER_FEATURES_ONLINE", "V1")
    print(f"Feature view: {user_fv.name}/{user_fv.version}")

    # Retrieve model version
    reg = Registry(session=session, database_name=DATABASE, schema_name=MODELS_SCHEMA)
    mv = reg.get_model(MODEL_NAME).version(MODEL_VERSION)
    print(f"Model version: {mv.model_name}/{mv.version_name}")

    print(f"\nDeploying service '{SERVICE_NAME}' on pool '{COMPUTE_POOL}' ...")
    print("(CPU models typically take ~10 minutes on first deploy)\n")

    mv.create_service(
        service_name=SERVICE_NAME,
        service_compute_pool=COMPUTE_POOL,
        ingress_enabled=True,
        # Maps the "predict" method to the Postgres-backed feature view.
        # Requests only need USER_ID; all other feature columns are fetched
        # automatically from the online store before the model is called.
        feature_sources_per_function={"predict": [user_fv]},
    )

    # Poll until the service is READY
    for attempt in range(30):
        services = mv.list_services()
        row = services[services["service_name"] == SERVICE_NAME]
        if not row.empty:
            status = row.iloc[0].get("status", "UNKNOWN")
            endpoint = row.iloc[0].get("inference_endpoint", "")
            print(f"  [{attempt * 10}s] status={status}")
            if status == "READY":
                print(f"\nService is READY.")
                print(f"Inference endpoint: {endpoint}")
                print(f"\nRun script 04 to test inference:")
                print(
                    f"  python scripts/04_test_inference.py "
                    f"--endpoint {endpoint} --token <your_pat>"
                )
                return
        time.sleep(10)

    print("Timed out waiting for READY. Check Snowsight → Model Registry → Services.")


if __name__ == "__main__":
    main()
