from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import clicks_router, features_router, products_router, recommend_router
from .services.snowflake import get_snowflake_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    settings = get_settings()
    print("Starting Content Recommendation API...")
    print(f"Mock mode: {settings.use_mock}")
    if not settings.use_mock:
        print(f"Snowflake Account: {settings.snowflake_account}")
    yield
    # Shutdown
    print("Shutting down...")
    get_snowflake_service().close()


app = FastAPI(
    title="Content Recommendation API",
    description="Real-time content recommendation using Snowflake Online Feature Serving",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(clicks_router)
app.include_router(recommend_router)
app.include_router(features_router)
app.include_router(products_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Content Recommendation API",
        "version": "1.0.0",
        "mock_mode": settings.use_mock,
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "snowflake_connected": not settings.use_mock,
        "mock_mode": settings.use_mock,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
