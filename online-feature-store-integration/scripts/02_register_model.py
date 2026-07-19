"""
Script 02: Log the UserEmbeddingModel to the Snowflake Model Registry.

The model is serialised via cloudpickle (CustomModel) and stored in
CONTENT_REC_DEMO.MODELS. Its signature is inferred from a small sample
DataFrame matching the feature view's output schema.

Run from the repo root:
    cd backend && uv run python ../online-feature-store-integration/scripts/02_register_model.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / "backend" / ".env")

# Allow `from model.user_embedding_model import ...`
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from snowflake.ml.model.model_signature import infer_signature
from snowflake.ml.registry import Registry
from snowflake.snowpark import Session

from model.user_embedding_model import (
    CATEGORY_COLS,
    DELTA_COLS,
    EMB_COLS,
    UserEmbeddingModel,
)

DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "CONTENT_REC_DEMO")
MODELS_SCHEMA = "MODELS"
MODEL_NAME = "USER_EMBEDDING_MODEL"
MODEL_VERSION = "V1"


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


def _make_sample_input(n: int = 4) -> pd.DataFrame:
    """Minimal sample matching the feature view's output schema."""
    rng = np.random.default_rng(0)
    data = {col: rng.uniform(0, 1, n) for col in CATEGORY_COLS}
    data["TOTAL_CLICKS"] = rng.integers(0, 100, n).astype(float)
    for col in DELTA_COLS:
        data[col] = rng.standard_normal(n)
    return pd.DataFrame(data)


def main() -> None:
    session = _build_session()
    print(f"Connected: {session.get_current_account()}")

    # Ensure MODELS schema exists
    session.sql(f"CREATE SCHEMA IF NOT EXISTS {DATABASE}.{MODELS_SCHEMA}").collect()

    model = UserEmbeddingModel()
    sample_input = _make_sample_input()
    sample_output = model.predict(sample_input)

    sig = infer_signature(sample_input, sample_output)
    print(f"Signature inputs  ({len(sig.inputs)}): {[f.name for f in sig.inputs]}")
    print(f"Signature outputs ({len(sig.outputs)}): {[f.name for f in sig.outputs]}")

    reg = Registry(
        session=session,
        database_name=DATABASE,
        schema_name=MODELS_SCHEMA,
    )

    mv = reg.log_model(
        model=model,
        model_name=MODEL_NAME,
        version_name=MODEL_VERSION,
        signatures={"predict": sig},
        comment=(
            "Two-Tower UserTower: user feature columns → 32-dim L2-normalised embedding. "
            "Deploy with feature_sources_per_function to enable automatic Online Feature "
            "Store lookup at inference time."
        ),
    )
    print(f"\nModel logged: {mv.model_name} / {mv.version_name}")
    print("Run script 03 to deploy with online feature store integration.")


if __name__ == "__main__":
    main()
