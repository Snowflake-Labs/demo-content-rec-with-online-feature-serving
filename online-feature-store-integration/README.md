# Online Feature Store Integration with Real-time Inference

This demo extends the main content-recommendation app to show how the Snowflake ML **Real-time Inference REST API** integrates directly with the **Postgres-backed Online Feature Store**.

**Reference**: [Deploy models for real-time inference — Online feature store integration](https://docs.snowflake.com/en/developer-guide/snowflake-ml/inference/real-time-inference-rest-api#online-feature-store-integration)

---

## What this demo adds

### Base demo (existing)
```
Client → FastAPI backend → manually calls fs.read_feature_view() → runs Two-Tower in Python → returns recommendations
```

### This demo
```
Client → Snowflake Inference Endpoint → automatically fetches features from Postgres online store → runs UserTower → returns embedding
```

By passing `feature_sources_per_function={"predict": [user_fv]}` to `create_service()`, the model service fetches all feature columns from the registered FeatureView automatically.  
**You only need to send `USER_ID` in the request.** No application-side feature hydration code needed.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  Request: {"dataframe_split": {"columns": ["USER_ID"], "data": [..]} │
└──────────────────────────┬───────────────────────────────────────────┘
                           │  USER_ID only
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│         Snowflake Inference Service (SPCS)                           │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  1. feature_sources_per_function lookup                        │  │
│  │     USER_ID → Postgres online store → all feature columns      │  │
│  └───────────────────────────┬────────────────────────────────────┘  │
│                              │  38 feature columns                   │
│  ┌───────────────────────────▼────────────────────────────────────┐  │
│  │  2. UserEmbeddingModel.predict(X)                              │  │
│  │     category_prefs(5) + log_clicks(1) + delta_embedding(32)    │  │
│  │     → UserTower MLP → L2-normalise → embedding(32)             │  │
│  └───────────────────────────┬────────────────────────────────────┘  │
└──────────────────────────────┼───────────────────────────────────────┘
                               │  EMB_0 .. EMB_31
                               ▼
                      Response: 32-dim user embedding
```

### Feature validation at deploy time

When `create_service()` runs, Snowflake validates that the FeatureView's columns match the model's input signature. Only matching columns are eligible for automatic lookup — mismatches surface immediately, not at request time.

---

## Directory Structure

```
online-feature-store-integration/
├── README.md
├── model/
│   ├── __init__.py
│   └── user_embedding_model.py   # Snowflake CustomModel wrapping UserTower
└── scripts/
    ├── 01_setup_postgres_feature_view.py   # Register Postgres-backed FeatureView
    ├── 02_register_model.py                # Log model to Model Registry
    ├── 03_deploy_with_feature_integration.py  # create_service() with feature lookup
    └── 04_test_inference.py                # Call endpoint with only USER_ID
```

---

## Prerequisites

1. Complete the **base demo setup** first (SQL scripts `snowflake/01-05`, `scripts/setup_feature_store.py`).
2. Create a Snowflake Postgres instance (used as the online store backend):
   ```sql
   CREATE SNOWFLAKE POSTGRES INSTANCE content_rec_pg;
   ```
3. `backend/.env` configured with Snowflake credentials.
4. `snowflake-ml-python >= 1.25.0` (already in `backend/pyproject.toml`).

---

## Run the Demo

All scripts are run from the `backend/` directory so `uv` can resolve the right virtual environment.

### Step 1 — Register the Postgres-backed FeatureView

```bash
cd backend
uv run python ../online-feature-store-integration/scripts/01_setup_postgres_feature_view.py
```

This flattens `DELTA_EMBEDDING[ARRAY]` into 32 scalar columns (`DELTA_0` … `DELTA_31`) and registers a `USER_FEATURES_ONLINE / V1` FeatureView with:

```python
OnlineConfig(enable=True, target_lag="10s", store_type=OnlineStoreType.POSTGRES)
```

### Step 2 — Log the model to the Model Registry

```bash
uv run python ../online-feature-store-integration/scripts/02_register_model.py
```

Logs `USER_EMBEDDING_MODEL / V1` to `CONTENT_REC_DEMO.MODELS`. The model signature is inferred automatically from a sample DataFrame matching the FeatureView schema.

### Step 3 — Deploy with Online Feature Store integration

```bash
uv run python ../online-feature-store-integration/scripts/03_deploy_with_feature_integration.py
```

The key call:

```python
mv.create_service(
    service_name="USER_EMBEDDING_SERVICE",
    service_compute_pool="SYSTEM_COMPUTE_POOL_CPU",
    ingress_enabled=True,
    feature_sources_per_function={"predict": [user_fv]},  # <— auto feature lookup
)
```

Deployment takes ~10 minutes. The script polls until the service is `READY` and prints the endpoint URL.

### Step 4 — Test inference with only USER_ID

```bash
uv run python ../online-feature-store-integration/scripts/04_test_inference.py \
    --endpoint https://<service-id>-<account>.snowflakecomputing.app \
    --token <your_pat_token>
```

The script runs three tests:

| Test | What it sends | Expected result |
|------|--------------|-----------------|
| Batch (3 users) | `USER_ID` only | 32-dim embedding per user, features auto-fetched |
| Feature override | `USER_ID` + `TOTAL_CLICKS=999` | Embedding differs from baseline |
| Latency (5 calls) | Single `USER_ID` | avg / p50 latency printed |

---

## Key API Concepts

### `feature_sources_per_function`

```python
# Only one FeatureView per function is supported (Public Preview)
feature_sources_per_function={"predict": [registered_fv]}
```

- Maps a model method name to a list of registered `FeatureView` objects.
- The FeatureView must be registered with `OnlineStoreType.POSTGRES`.
- At inference time the service resolves the entity key (`USER_ID`) against the online store and appends the matching feature columns before calling the method.

### Feature override

If you include a feature column in the request alongside the entity key, that value takes precedence over the online store lookup for that column. All other features are still fetched automatically.

```python
# TOTAL_CLICKS comes from the request; everything else from the online store
payload = {
    "dataframe_split": {
        "columns": ["USER_ID", "TOTAL_CLICKS"],
        "data": [["user_123", 999.0]],
    }
}
```

### Authentication

```python
headers = {"Authorization": f'Snowflake Token="{pat_token}"'}
```

Use a Programmatic Access Token (PAT). See Snowsight → Admin → Security → PATs.
