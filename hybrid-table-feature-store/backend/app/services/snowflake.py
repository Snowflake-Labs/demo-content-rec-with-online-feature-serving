# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Snowflake Feature Store service with Online Feature Serving.

Uses the Snowflake ML Feature Store Python API for feature retrieval.
Reference: https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/create-and-serve-online-features-python
"""

import time
from datetime import datetime
from functools import lru_cache
from typing import Any

from ..config import Settings, get_settings
from ..models.schemas import (
    EMBEDDING_DIM,
    Product,
    ProductWithEmbedding,
    UserFeatures,
    UserFeaturesWithEmbedding,
)
from .embeddings import (
    compute_item_embedding,
    compute_user_delta_embedding,
    get_user_embeddings,
)


class SnowflakeService:
    """Service for interacting with Snowflake Feature Store."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._session: Any = None
        self._feature_store: Any = None
        self._feature_view: Any = None
        self._mock_products: dict[str, Product] = {}
        self._mock_item_embeddings: dict[str, ProductWithEmbedding] = {}
        self._mock_user_features: dict[str, UserFeatures] = {}
        self._mock_user_delta_embeddings: dict[str, list[float]] = {}
        self._init_mock_data()

    def _init_mock_data(self):
        """Initialize mock data for development/demo without Snowflake."""
        # Mock products
        mock_products_data = [
            # Electronics
            ("PROD001", "Wireless Bluetooth Headphones", "Electronics", 299.99, 4.5, 1250),
            ("PROD002", '4K Ultra HD Smart TV 55"', "Electronics", 799.99, 4.7, 890),
            ("PROD003", "Portable Bluetooth Speaker", "Electronics", 149.99, 4.3, 2100),
            ("PROD004", "Wireless Gaming Mouse", "Electronics", 79.99, 4.6, 3200),
            ("PROD005", "Smart Watch Pro", "Electronics", 449.99, 4.4, 1800),
            # Fashion
            ("PROD006", "Premium Leather Jacket", "Fashion", 399.99, 4.8, 560),
            ("PROD007", "Classic Denim Jeans", "Fashion", 89.99, 4.2, 4500),
            ("PROD008", "Running Sneakers", "Fashion", 129.99, 4.5, 2800),
            ("PROD009", "Wool Blend Sweater", "Fashion", 79.99, 4.3, 1200),
            ("PROD010", "Designer Sunglasses", "Fashion", 199.99, 4.6, 980),
            # Home
            ("PROD011", "Espresso Coffee Machine", "Home", 599.99, 4.7, 750),
            ("PROD012", "Air Fryer XL", "Home", 159.99, 4.4, 5600),
            ("PROD013", "Robot Vacuum Cleaner", "Home", 449.99, 4.3, 2100),
            ("PROD014", "Memory Foam Pillow Set", "Home", 69.99, 4.5, 8900),
            ("PROD015", "Stainless Steel Cookware Set", "Home", 299.99, 4.6, 1450),
            # Sports
            ("PROD016", "Yoga Mat Premium", "Sports", 49.99, 4.7, 6700),
            ("PROD017", "Adjustable Dumbbell Set", "Sports", 349.99, 4.5, 1890),
            ("PROD018", "Camping Tent 4-Person", "Sports", 199.99, 4.4, 920),
            ("PROD019", "Mountain Bike Helmet", "Sports", 89.99, 4.6, 2300),
            ("PROD020", "Fitness Tracker Band", "Sports", 79.99, 4.2, 4100),
            # Books
            ("PROD021", "Bestseller Novel Collection", "Books", 59.99, 4.8, 3400),
            ("PROD022", "Programming Guide Bundle", "Books", 89.99, 4.5, 1200),
            ("PROD023", "Cookbook: World Cuisines", "Books", 39.99, 4.6, 2800),
            ("PROD024", "Photography Art Book", "Books", 49.99, 4.7, 890),
            ("PROD025", "Business Strategy Guide", "Books", 34.99, 4.3, 1560),
        ]

        for pid, name, category, price, rating, reviews in mock_products_data:
            product = Product(
                product_id=pid,
                name=name,
                category=category,
                description=f"High-quality {name.lower()} for your needs",
                price=price,
                image_url=f"https://picsum.photos/seed/{pid}/400/400",
                rating=rating,
                review_count=reviews,
            )
            self._mock_products[pid] = product

            # Pre-compute item embeddings (batch operation in production)
            embedding = compute_item_embedding(product)
            self._mock_item_embeddings[pid] = ProductWithEmbedding(
                **product.model_dump(), embedding=embedding
            )

        # Initialize demo user with empty features
        self._mock_user_features["demo_user"] = UserFeatures(
            user_id="demo_user",
            recent_click_ids=[],
            category_preference={},
            total_clicks=0,
            last_click_timestamp=None,
        )
        self._mock_user_delta_embeddings["demo_user"] = [0.0] * EMBEDDING_DIM

    def _get_session(self) -> Any:
        """Get Snowpark session (lazy initialization)."""
        if self.settings.use_mock:
            return None

        if self._session is None:
            from snowflake.snowpark import Session

            connection_params = {
                "account": self.settings.snowflake_account,
                "user": self.settings.snowflake_user,
                "warehouse": self.settings.snowflake_warehouse,
                "database": self.settings.snowflake_database,
                "schema": self.settings.snowflake_schema,
                "role": self.settings.snowflake_role,
            }

            # Authentication: PAT or Password
            if self.settings.snowflake_token:
                connection_params["token"] = self.settings.snowflake_token
                connection_params["authenticator"] = "PROGRAMMATIC_ACCESS_TOKEN"
            elif self.settings.snowflake_password:
                connection_params["password"] = self.settings.snowflake_password
            else:
                raise ValueError(
                    "No authentication method configured. "
                    "Set SNOWFLAKE_TOKEN (PAT) or SNOWFLAKE_PASSWORD"
                )
            self._session = Session.builder.configs(connection_params).create()

        return self._session

    def _get_feature_store(self) -> Any:
        """Get Feature Store instance (lazy initialization)."""
        if self.settings.use_mock:
            return None

        if self._feature_store is None:
            from snowflake.ml.feature_store import FeatureStore

            session = self._get_session()
            self._feature_store = FeatureStore(
                session=session,
                database=self.settings.snowflake_database,
                name=self.settings.snowflake_schema,
                default_warehouse=self.settings.snowflake_warehouse,
            )

        return self._feature_store

    def _get_feature_view(self):
        """Get the user click features FeatureView."""
        if self.settings.use_mock:
            return None

        if self._feature_view is None:
            fs = self._get_feature_store()
            # Get the feature view by name and version
            self._feature_view = fs.get_feature_view(
                name="USER_CLICK_FEATURES",
                version="1",  # Adjust version as needed
            )

        return self._feature_view

    async def get_all_products(self) -> list[Product]:
        """Get all products from the catalog."""
        if self.settings.use_mock:
            return list(self._mock_products.values())

        session = self._get_session()
        df = session.table("RAW_DATA.PRODUCTS").to_pandas()

        products = []
        for _, row in df.iterrows():
            products.append(
                Product(
                    product_id=row["PRODUCT_ID"],
                    name=row["NAME"],
                    category=row["CATEGORY"],
                    description=row.get("DESCRIPTION"),
                    price=float(row["PRICE"]),
                    image_url=row.get("IMAGE_URL"),
                    rating=float(row.get("RATING", 4.0)),
                    review_count=int(row.get("REVIEW_COUNT", 0)),
                )
            )
        return products

    async def get_product(self, product_id: str) -> Product | None:
        """Get a single product by ID."""
        if self.settings.use_mock:
            return self._mock_products.get(product_id)

        session = self._get_session()
        df = session.table("RAW_DATA.PRODUCTS").filter(f"PRODUCT_ID = '{product_id}'").to_pandas()

        if len(df) > 0:
            row = df.iloc[0]
            return Product(
                product_id=row["PRODUCT_ID"],
                name=row["NAME"],
                category=row["CATEGORY"],
                description=row.get("DESCRIPTION"),
                price=float(row["PRICE"]),
                image_url=row.get("IMAGE_URL"),
                rating=float(row.get("RATING", 4.0)),
                review_count=int(row.get("REVIEW_COUNT", 0)),
            )
        return None

    async def get_item_embedding(self, product_id: str) -> ProductWithEmbedding | None:
        """Get pre-computed item embedding (batch computed in production)."""
        if self.settings.use_mock:
            return self._mock_item_embeddings.get(product_id)

        product = await self.get_product(product_id)
        if product:
            embedding = compute_item_embedding(product)
            return ProductWithEmbedding(**product.model_dump(), embedding=embedding)
        return None

    async def get_all_item_embeddings(self) -> dict[str, ProductWithEmbedding]:
        """Get all item embeddings (for similarity search)."""
        if self.settings.use_mock:
            return self._mock_item_embeddings.copy()

        products = await self.get_all_products()
        result = {}
        for product in products:
            embedding = compute_item_embedding(product)
            result[product.product_id] = ProductWithEmbedding(
                **product.model_dump(), embedding=embedding
            )
        return result

    async def get_user_features(self, user_id: str) -> tuple[UserFeaturesWithEmbedding, float]:
        """
        Get user features including embeddings via Online Feature Serving.

        Uses the Snowflake ML Feature Store Python API:
        fs.read_feature_view(feature_view, keys, store_type=StoreType.ONLINE)

        Reference: https://docs.snowflake.com/ja/developer-guide/snowflake-ml/feature-store/create-and-serve-online-features-python

        Returns features and latency in milliseconds.
        """
        start_time = time.time()

        if self.settings.use_mock:
            # Return mock features with embeddings
            if user_id not in self._mock_user_features:
                self._mock_user_features[user_id] = UserFeatures(
                    user_id=user_id,
                    recent_click_ids=[],
                    category_preference={},
                    total_clicks=0,
                    last_click_timestamp=None,
                )
                self._mock_user_delta_embeddings[user_id] = [0.0] * EMBEDDING_DIM

            features = self._mock_user_features[user_id]
            delta = self._mock_user_delta_embeddings.get(user_id, [0.0] * EMBEDDING_DIM)

            # Compute embeddings
            embeddings = get_user_embeddings(
                user_id=user_id,
                category_preference=features.category_preference,
                total_clicks=features.total_clicks,
                current_delta=delta,
            )

            latency = (time.time() - start_time) * 1000

            return UserFeaturesWithEmbedding(
                **features.model_dump(), embeddings=embeddings
            ), latency

        # Use Snowflake ML Feature Store Python API
        from snowflake.ml.feature_store import StoreType

        fs = self._get_feature_store()
        fv = self._get_feature_view()

        # Read features from Online Feature Store
        # This uses the low-latency online serving infrastructure
        result_df = fs.read_feature_view(
            feature_view=fv,
            keys=[[user_id]],  # List of key values
            feature_names=[
                "RECENT_CLICK_IDS",
                "CATEGORY_PREFERENCE",
                "TOTAL_CLICKS",
                "LAST_CLICK_TIMESTAMP",
            ],
            store_type=StoreType.ONLINE,  # Use online store for low latency
        ).to_pandas()

        latency = (time.time() - start_time) * 1000

        if len(result_df) > 0:
            row = result_df.iloc[0]
            features = UserFeatures(
                user_id=user_id,
                recent_click_ids=row.get("RECENT_CLICK_IDS", []) or [],
                category_preference=row.get("CATEGORY_PREFERENCE", {}) or {},
                total_clicks=int(row.get("TOTAL_CLICKS", 0) or 0),
                last_click_timestamp=row.get("LAST_CLICK_TIMESTAMP"),
            )
        else:
            features = UserFeatures(
                user_id=user_id,
                recent_click_ids=[],
                category_preference={},
                total_clicks=0,
                last_click_timestamp=None,
            )

        # Get delta embedding (would be stored in Feature Store in production)
        delta = [0.0] * EMBEDDING_DIM

        embeddings = get_user_embeddings(
            user_id=user_id,
            category_preference=features.category_preference,
            total_clicks=features.total_clicks,
            current_delta=delta,
        )

        return UserFeaturesWithEmbedding(**features.model_dump(), embeddings=embeddings), latency

    async def record_click_and_update_features(
        self, user_id: str, product_id: str
    ) -> tuple[UserFeaturesWithEmbedding, float, float]:
        """
        Record a click event and update user features + delta embedding.
        Returns updated features, total latency, and delta update latency in ms.
        """
        start_time = time.time()

        # Get product and its embedding
        product = await self.get_product(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        category = product.category
        item_with_embedding = await self.get_item_embedding(product_id)

        if self.settings.use_mock:
            # Update mock features
            if user_id not in self._mock_user_features:
                self._mock_user_features[user_id] = UserFeatures(
                    user_id=user_id,
                    recent_click_ids=[],
                    category_preference={},
                    total_clicks=0,
                    last_click_timestamp=None,
                )
                self._mock_user_delta_embeddings[user_id] = [0.0] * EMBEDDING_DIM

            features = self._mock_user_features[user_id]

            # Update recent clicks (prepend, keep last 10)
            new_clicks = [product_id] + [
                pid for pid in features.recent_click_ids if pid != product_id
            ][:9]

            # Update category preference
            new_prefs = dict(features.category_preference)
            new_prefs[category] = new_prefs.get(category, 0) + 1

            # Create updated features
            updated_features = UserFeatures(
                user_id=user_id,
                recent_click_ids=new_clicks,
                category_preference=new_prefs,
                total_clicks=features.total_clicks + 1,
                last_click_timestamp=datetime.now(),
            )
            self._mock_user_features[user_id] = updated_features

            # Update delta embedding with clicked item embedding (REAL-TIME!)
            delta_start = time.time()
            current_delta = self._mock_user_delta_embeddings.get(user_id, [0.0] * EMBEDDING_DIM)
            new_delta = compute_user_delta_embedding(
                current_delta=current_delta,
                clicked_item_embedding=item_with_embedding.embedding,
                decay_factor=0.7,
            )
            self._mock_user_delta_embeddings[user_id] = new_delta
            delta_latency = (time.time() - delta_start) * 1000

            # Compute full embeddings
            embeddings = get_user_embeddings(
                user_id=user_id,
                category_preference=updated_features.category_preference,
                total_clicks=updated_features.total_clicks,
                current_delta=new_delta,
            )

            total_latency = (time.time() - start_time) * 1000

            return (
                UserFeaturesWithEmbedding(**updated_features.model_dump(), embeddings=embeddings),
                total_latency,
                delta_latency,
            )

        # Production: Update features in Snowflake
        session = self._get_session()

        # Insert click event
        session.sql(f"""
            INSERT INTO CLICK_EVENTS (user_id, product_id, category)
            VALUES ('{user_id}', '{product_id}', '{category}')
        """).collect()

        # Call stored procedure to update user features
        session.sql(f"""
            CALL UPDATE_USER_FEATURES('{user_id}', '{product_id}', '{category}')
        """).collect()

        # Note: In production with proper target_lag configuration,
        # the online store refreshes automatically via Snowflake's internal mechanisms.
        # Manual refresh is not needed as target_lag="10 seconds" handles synchronization.

        # Get updated features from online store
        features, _ = await self.get_user_features(user_id)
        total_latency = (time.time() - start_time) * 1000

        return features, total_latency, 0.0

    def close(self):
        """Close the Snowflake session."""
        if self._session:
            self._session.close()
            self._session = None
            self._feature_store = None
            self._feature_view = None


@lru_cache
def get_snowflake_service() -> SnowflakeService:
    """Get singleton SnowflakeService instance."""
    return SnowflakeService(get_settings())
