from .clicks import router as clicks_router
from .features import router as features_router
from .products import router as products_router
from .recommend import router as recommend_router

__all__ = ["clicks_router", "recommend_router", "features_router", "products_router"]
