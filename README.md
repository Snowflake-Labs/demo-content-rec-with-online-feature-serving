# Demo: Content Recommendation with Snowflake Online Feature Serving

Real-time product recommendation demos powered by Snowflake Online Feature Serving. This repository contains two independent demo implementations that showcase different approaches to serving features at inference time.

## Demos

| Demo | Online Store Type | Inference | Frontend | Status |
|------|------------------|-----------|----------|--------|
| [hybrid-table-feature-store](./hybrid-table-feature-store/) | Hybrid Table (default) | FastAPI + Python SDK | React + Vite | Complete |
| [online-feature-store-integration](./online-feature-store-integration/) | Postgres | SPCS REST API + `feature_sources_per_function` | Next.js (Snowflake App) | Complete (SPCS deploy TBD) |

## Key Differences

| | Hybrid Table Feature Store | Online Feature Store Integration |
|---|---|---|
| **Online Store backend** | Snowflake Hybrid Table (`StoreType.ONLINE`) | Snowflake Postgres (`OnlineStoreType.POSTGRES`) |
| **Feature retrieval** | Application calls `fs.read_feature_view()` | Inference service auto-fetches via `feature_sources_per_function` |
| **Model execution** | Python (PyTorch in FastAPI) | SPCS Model Serving (REST API) |
| **Feature override** | N/A (app manages all features) | Send feature column in request to override store value |
| **Request payload** | All features passed explicitly | Only entity ID (`USER_ID`) + item features |
| **Deployment** | `uvicorn` + `npm run dev` | `snow app deploy` (Snowflake App Runtime) |
| **Auth to inference** | N/A (local Python call) | PAT token / SPCS service token |

## Architecture Comparison

```
Demo 1: Hybrid Table Feature Store
─────────────────────────────────────────────
React UI → FastAPI Backend → fs.read_feature_view(store_type=ONLINE)
                           → Two-Tower model (in-process PyTorch)
                           → Cosine similarity ranking

Demo 2: Online Feature Store Integration
─────────────────────────────────────────────
Next.js UI → API Route → SPCS Inference Endpoint (/predict)
                              │
                              ├─ feature_sources_per_function (auto-fetch from Postgres store)
                              ├─ Feature Override (optional PREFERRED_CATEGORY_ENC)
                              └─ Model predict → ranked recommendations
```

## Project Structure

```
├── hybrid-table-feature-store/           # Demo 1
│   ├── backend/                          #   FastAPI + Two-Tower PyTorch model
│   ├── frontend/                         #   React + Vite + TypeScript
│   ├── scripts/                          #   Feature Store setup (Python API)
│   ├── snowflake/                        #   SQL scripts (database, tables, data)
│   └── README.md
│
├── online-feature-store-integration/     # Demo 2
│   ├── model/                            #   Snowflake CustomModel (UserTower)
│   ├── scripts/                          #   Model registry + service deployment
│   ├── snowflake-app/                    #   Next.js Snowflake App (UI)
│   └── README.md
│
├── .github/                              # CI (lint)
└── README.md                             # This file
```

## Prerequisites

- Python 3.11+ (3.12 recommended)
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Snowflake account with Online Feature Store enabled
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation) (`snow`) for Demo 2

## Quick Start

Each demo has its own README with setup instructions:

- **Demo 1**: [`hybrid-table-feature-store/README.md`](./hybrid-table-feature-store/README.md)
- **Demo 2**: [`online-feature-store-integration/README.md`](./online-feature-store-integration/README.md)

## References

- [Snowflake Online Feature Store](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/online-feature-store)
- [Real-time Inference REST API](https://docs.snowflake.com/en/developer-guide/snowflake-ml/inference/real-time-inference-rest-api)
- [Online Feature Store Integration (feature_sources_per_function)](https://docs.snowflake.com/en/developer-guide/snowflake-ml/inference/real-time-inference-rest-api#online-feature-store-integration)
- [Snowflake App Runtime](https://docs.snowflake.com/en/developer-guide/snowflake-apps/overview)

## License

Copyright (c) Snowflake Inc. All rights reserved. Licensed under the Apache 2.0 license.

**Disclaimer: This demo is not an official Snowflake product.**
