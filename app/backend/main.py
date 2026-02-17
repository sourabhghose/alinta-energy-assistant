"""Main FastAPI application for Alinta Energy Assistant."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import os
from pathlib import Path

from .api.routes import router
from .config import settings, validate_config

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Validate configuration
try:
    validate_config()
    logger.info("Configuration validated successfully")
except Exception as e:
    logger.error(f"Configuration validation failed: {str(e)}")
    # Continue anyway - some checks may fail in dev environment

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered customer support assistant for Alinta Energy",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["chat"])

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {'DEBUG' if settings.debug else 'PRODUCTION'}")
    logger.info(f"Vector Search Index: {settings.vector_search_index}")
    logger.info(f"LLM Model: {settings.llm_model}")


# Serve React frontend (after build)
frontend_dist_path = Path(__file__).parent.parent / "dist"

if frontend_dist_path.exists() and frontend_dist_path.is_dir():
    logger.info(f"Serving frontend from: {frontend_dist_path}")

    # Serve static files (JS, CSS, images, etc.)
    app.mount(
        "/assets",
        StaticFiles(directory=str(frontend_dist_path / "assets")),
        name="assets"
    )

    # Serve index.html for all other routes (SPA support)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React frontend for all non-API routes."""
        # Don't intercept API routes or static files
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("redoc"):
            return {"error": "Not found"}

        # Serve index.html
        index_path = frontend_dist_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        else:
            return {"error": "Frontend not built"}

else:
    logger.warning(f"Frontend dist directory not found at: {frontend_dist_path}")
    logger.warning("Run 'cd frontend && npm run build' to build the frontend")

    # Fallback root route
    @app.get("/")
    async def root():
        """Root endpoint when frontend is not built."""
        return {
            "message": "Alinta Energy Assistant API",
            "version": settings.app_version,
            "docs": "/docs",
            "api": "/api/",
            "note": "Frontend not built. Run 'cd frontend && npm run build'"
        }


if __name__ == "__main__":
    import uvicorn

    # Get port from environment (Databricks Apps requirement)
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
