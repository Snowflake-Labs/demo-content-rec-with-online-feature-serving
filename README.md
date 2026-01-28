# Content Recommendation with Snowflake Online Feature Serving

Real-time product recommendation demo powered by Snowflake Online Feature Serving and Two-Tower architecture. This application demonstrates how to build a personalized recommendation system with real-time embedding updates based on user click behavior.

## Two-Tower Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Two-Tower Recommendation Model                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────┐              ┌─────────────────────┐             │
│   │     User Tower      │              │     Item Tower      │             │
│   │                     │              │                     │             │
│   │ ┌─────────────────┐ │              │ ┌─────────────────┐ │             │
│   │ │ Base Embedding  │ │  Weighted    │ │ Item Embedding  │ │             │
│   │ │ (Batch: Daily)  │ │  Combination │ │ (Batch: Daily)  │ │             │
│   │ └────────┬────────┘ │              │ └────────┬────────┘ │             │
│   │          │ 60%      │              │          │          │             │
│   │          ▼          │              │          │          │             │
│   │ ┌─────────────────┐ │              │          │          │             │
│   │ │ Delta Embedding │ │              │          │          │             │
│   │ │ (Real-time)     │ │              │          │          │             │
│   │ └────────┬────────┘ │              │          │          │             │
│   │          │ 40%      │              │          │          │             │
│   │          ▼          │              │          │          │             │
│   │ ┌─────────────────┐ │              │          │          │             │
│   │ │Combined Embedding│◀──────────────┼──────────┼──────────┘             │
│   │ │   (32-dim)      │ │   Cosine     │          │                        │
│   │ └────────┬────────┘ │  Similarity  │          │                        │
│   └──────────┼──────────┘              └──────────┼──────────┘             │
│              │                                    │                        │
│              └────────────────┬───────────────────┘                        │
│                               ▼                                            │
│                    ┌─────────────────────┐                                 │
│                    │   Ranked Products   │                                 │
│                    │   (Top-N by score)  │                                 │
│                    └─────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Two-Tower DNN Architecture

**Same neural network logic is used in both production (Snowflake) and demo (mock) environments.**

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Two-Tower Deep Neural Network                   │
├─────────────────────────────────┬───────────────────────────────────┤
│          User Tower             │           Item Tower              │
│                                 │                                   │
│   Input: 38 dimensions          │   Input: 8 dimensions             │
│   - category_prefs (5)          │   - category one-hot (5)          │
│   - total_clicks (1)            │   - price (1)                     │
│   - delta_embedding (32)        │   - rating (1)                    │
│                                 │   - popularity (1)                │
│         ↓                       │         ↓                         │
│   [Linear 38 → 64 + ReLU]       │   [Linear 8 → 64 + ReLU]          │
│   [Linear 64 → 64 + ReLU]       │   [Linear 64 → 64 + ReLU]         │
│   [Linear 64 → 32]              │   [Linear 64 → 32]                │
│   [L2 Normalize]                │   [L2 Normalize]                  │
│         ↓                       │         ↓                         │
│   User Embedding (32-dim)       │   Item Embedding (32-dim)         │
└─────────────────────────────────┴───────────────────────────────────┘
                    ↓                           ↓
              Cosine Similarity = dot(user_emb, item_emb)
```

| Component | DNN Architecture | Frequency | Latency |
|-----------|------------------|-----------|---------|
| **Item Tower** | MLP: 8 → 64 → 64 → 32 | Batch (Daily) | ~1ms |
| **User Tower** | MLP: 38 → 64 → 64 → 32 | **Real-time** | ~1ms |
| **Delta Embedding** | Exponential moving average | **Real-time** | < 1ms |

## Features

- **Two-Tower Model**: User and Item embeddings for semantic similarity matching
- **Real-time Delta Updates**: User embedding updates instantly on each click
- **Low-latency Feature Serving**: Online Feature Serving provides sub-100ms feature retrieval
- **Embedding Visualization**: Debug panel shows real-time embedding heatmaps
- **Similarity Scores**: Each recommendation shows its cosine similarity match percentage
- **Consistent Logic**: Same embedding algorithm in production and demo modes
- **Mock Mode**: Works without Snowflake connection for development

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              React Frontend                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────────┐ │
│  │  Product Grid   │  │  Recommend Section │  │  Feature Debug Panel      │ │
│  │                 │  │  (with scores)    │  │  (Embeddings + Latency)   │ │
│  └────────┬────────┘  └────────┬─────────┘  └─────────────────────────────┘ │
└───────────┼────────────────────┼────────────────────────────────────────────┘
            │                    │
            ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI Backend                                    │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────────┐ │
│  │  POST /click    │  │  GET /recommend   │  │  Embedding Service         │ │
│  │  + Delta Update │  │  + Cosine Sim    │  │  (Two-Tower computation)   │ │
│  └────────┬────────┘  └────────┬─────────┘  └─────────────────────────────┘ │
└───────────┼────────────────────┼────────────────────────────────────────────┘
            │                    │
            ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Snowflake Feature Store                              │
│  ┌─────────────────┐  ┌──────────────────────────────────────────────────┐  │
│  │  Item Embeddings │  │           User Features + Embeddings             │  │
│  │  (Batch computed)│  │  - base_embedding (32-dim, batch)               │  │
│  └─────────────────┘  │  - delta_embedding (32-dim, real-time)           │  │
│                       │  - category_preference (dict)                     │  │
│                       │  - recent_click_ids (array)                       │  │
│                       └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Frontend**: React 18, TypeScript, Framer Motion, Vite
- **Backend**: Python, FastAPI, uv (package manager)
- **ML**: PyTorch Two-Tower DNN with 32-dimensional embeddings
- **Feature Store**: Snowflake ML Feature Store with Online Serving
- **Styling**: CSS Modules with custom design system

## Prerequisites

- Python 3.11+ (3.12 recommended)
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Snowflake account (optional - mock mode available for development)

## Quick Start

### 1. Clone and Setup Backend

```bash
cd backend

# Install Python 3.12 if needed (using uv)
uv python install 3.12

# Install dependencies with uv
uv sync

# Copy environment file and configure
cp env.example .env
# Edit .env with your settings (USE_MOCK=true for development)

# Start the backend server
uv run uvicorn app.main:app --reload --port 8000
```

### 2. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Access the Application

Open http://localhost:5173 in your browser.

## Snowflake Setup (Production)

To use real Snowflake Feature Store with Online Serving:

### 1. Run SQL Scripts

```bash
# Execute in Snowflake Worksheets in order:
snowflake/01_create_database.sql
snowflake/02_create_feature_store.sql
snowflake/03_create_entities.sql
snowflake/04_create_feature_views.sql  # Just prepares tables
snowflake/05_sample_data.sql
```

### 2. Setup Feature Store with Python API

The Feature View with Online Serving is created using the Python API:

```bash
cd backend
uv run python ../scripts/setup_feature_store.py
```

This script uses the [Snowflake ML Feature Store Python API](https://docs.snowflake.com/ja/developer-guide/snowflake-ml/feature-store/create-and-serve-online-features-python):

```python
from snowflake.ml.feature_store import FeatureStore, FeatureView, Entity
from snowflake.ml.feature_store.feature_view import OnlineConfig
from snowflake.ml.feature_store import StoreType

# Create Feature Store
fs = FeatureStore(session=session, database="CONTENT_REC_DEMO", name="FEATURES")

# Register Feature View with Online Serving
fv = FeatureView(
    name="USER_CLICK_FEATURES",
    entities=[user_entity],
    feature_df=session.table("USER_FEATURES"),
    refresh_freq="1 minute",
)
fs.register_feature_view(feature_view=fv, version="1")

# Enable Online Serving with target lag
fs.update_feature_view(
    name="USER_CLICK_FEATURES",
    version="1",
    online_config=OnlineConfig(enable=True, target_lag="10 seconds")
)

# Read features from Online Store (low latency!)
result = fs.read_feature_view(
    feature_view=fv,
    keys=[["user_123"]],
    feature_names=["recent_click_ids", "category_preference"],
    store_type=StoreType.ONLINE  # Use online store
)
```

### 3. Configure Backend

Update `backend/.env`:

```env
USE_MOCK=false
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/products` | GET | Get all products |
| `/api/products/{id}` | GET | Get product by ID |
| `/api/categories` | GET | Get all categories |
| `/api/click` | POST | Record click + update delta embedding |
| `/api/recommend/{user_id}` | GET | Get recommendations with similarity scores |
| `/api/features/{user_id}` | GET | Get features + embeddings (debug) |

## How It Works

### Click Flow (Real-time Delta Update)

1. User clicks a product in the UI
2. Frontend sends POST to `/api/click`
3. Backend:
   - Records click event
   - Gets clicked item's embedding (pre-computed)
   - Updates user delta: `new_delta = 0.7 * old_delta + 0.3 * item_embedding`
   - Updates category preferences
4. Returns updated features + embeddings
5. Frontend refreshes recommendations

### Recommendation Flow (Two-Tower Similarity)

1. Frontend requests `/api/recommend/{user_id}`
2. Backend fetches user features via Online Feature Serving
3. Computes combined embedding: `0.6 * base + 0.4 * delta`
4. Calculates cosine similarity with all item embeddings
5. Returns top-N products sorted by similarity score

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── config.py         # Settings management
│   │   ├── models/
│   │   │   └── schemas.py    # Pydantic models (with embeddings)
│   │   ├── routers/
│   │   │   ├── clicks.py     # Click + delta update
│   │   │   ├── recommend.py  # Two-Tower recommendations
│   │   │   ├── features.py   # Feature debugging
│   │   │   └── products.py   # Product catalog
│   │   └── services/
│   │       ├── embeddings.py # Two-Tower embedding logic
│   │       ├── snowflake.py  # Feature Store connection
│   │       └── recommender.py # Cosine similarity ranking
│   ├── pyproject.toml        # Python dependencies (uv)
│   └── env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Header.tsx
│   │   │   ├── ProductCard.tsx
│   │   │   ├── ProductGrid.tsx
│   │   │   ├── RecommendSection.tsx  # Shows similarity scores
│   │   │   └── FeatureDebugPanel.tsx # Embedding visualization
│   │   ├── hooks/
│   │   │   └── useRecommendation.ts
│   │   └── api/
│   │       ├── client.ts
│   │       └── types.ts
│   └── package.json
└── snowflake/
    ├── 01_create_database.sql
    ├── 02_create_feature_store.sql
    ├── 03_create_entities.sql
    ├── 04_create_feature_views.sql
    └── 05_sample_data.sql
```

## Debug Panel Features

The debug panel (right side) has three tabs:

1. **Features**: Shows raw features (clicks, category preferences)
2. **Embeddings**: Visualizes base, delta, and combined embeddings as heatmaps
3. **Latency**: Shows pipeline latency breakdown:
   - Feature Serving latency (Online Feature Serving)
   - Embedding compute time
   - Similarity calculation time
   - Delta update time

## Demo Walkthrough

1. **Initial State**: Open the app - recommendations are based on popularity (cold start)
2. **Click Electronics**: Click a few electronics products
3. **Watch Delta Update**: See the delta embedding change in the debug panel
4. **See Personalization**: Recommendations shift to show more Electronics products
5. **Click Fashion**: Click some fashion products
6. **Watch Blend**: The combined embedding balances your interests
7. **Check Latency**: See real-time feature serving latency (target: < 100ms)

## License

MIT
