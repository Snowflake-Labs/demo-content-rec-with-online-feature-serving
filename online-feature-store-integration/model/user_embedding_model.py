"""
UserEmbeddingModel — Snowflake CustomModel wrapping the Two-Tower UserTower.

Feature columns supplied automatically from the Postgres-backed FeatureView
when using `feature_sources_per_function` in `create_service()`:

    CATEGORY_ELECTRONICS, CATEGORY_FASHION, CATEGORY_HOME,
    CATEGORY_SPORTS, CATEGORY_BOOKS  — normalized click share per category
    TOTAL_CLICKS                     — cumulative click count
    DELTA_0 .. DELTA_31              — real-time EMA delta embedding (32-dim)

Output columns:
    EMB_0 .. EMB_31                  — L2-normalized 32-dim user embedding
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

from snowflake.ml.model import custom_model

CATEGORY_COLS = [
    "CATEGORY_ELECTRONICS",
    "CATEGORY_FASHION",
    "CATEGORY_HOME",
    "CATEGORY_SPORTS",
    "CATEGORY_BOOKS",
]
DELTA_COLS = [f"DELTA_{i}" for i in range(32)]
EMB_COLS = [f"EMB_{i}" for i in range(32)]

# Input dimensionality: 5 category prefs + 1 log-clicks + 32 delta embedding
_INPUT_DIM = 38


class _UserTower(nn.Module):
    """Identical architecture to backend/app/services/embeddings.py UserTower."""

    def __init__(self) -> None:
        super().__init__()
        torch.manual_seed(42)
        self.fc1 = nn.Linear(_INPUT_DIM, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, 32)
        for layer in (self.fc1, self.fc2, self.fc3):
            nn.init.xavier_uniform_(layer.weight)
            nn.init.zeros_(layer.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return F.normalize(x, p=2, dim=-1)


class UserEmbeddingModel(custom_model.CustomModel):
    """
    Snowflake CustomModel: user feature columns → 32-dim L2-normalised embedding.

    When deployed with `feature_sources_per_function={"predict": [user_fv]}`,
    requests only need to include USER_ID; all feature columns are fetched
    automatically from the Postgres-backed online feature store.
    """

    def __init__(
        self,
        context: custom_model.ModelContext = custom_model.ModelContext(),
    ) -> None:
        super().__init__(context)
        self._tower = _UserTower()
        self._tower.eval()

    @custom_model.inference_api
    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        category_prefs = X[CATEGORY_COLS].values.astype(np.float32)          # (N, 5)
        log_clicks = (
            np.log1p(X["TOTAL_CLICKS"].values.astype(np.float32))
            .reshape(-1, 1)
        )                                                                      # (N, 1)
        delta = X[DELTA_COLS].values.astype(np.float32)                      # (N, 32)

        features = np.concatenate([category_prefs, log_clicks, delta], axis=1)  # (N, 38)

        with torch.no_grad():
            embedding = self._tower(torch.from_numpy(features)).numpy()       # (N, 32)

        return pd.DataFrame(embedding, columns=EMB_COLS, index=X.index)
