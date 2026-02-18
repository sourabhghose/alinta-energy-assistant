"""FastAPI application for Alinta Energy Assistant."""

from fastapi import FastAPI
import os

# This will be used by uvicorn when run with: uvicorn app:app
app = FastAPI(title="Alinta Energy Assistant", version="1.0.0")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Alinta Energy Assistant API",
        "status": "running",
        "version": "1.0.0",
        "port": os.getenv("PORT", "unknown")
    }

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "alinta-energy-assistant"
    }

@app.get("/api/v1/health")
async def health_v1():
    """Health check endpoint (v1)."""
    return {
        "status": "healthy",
        "service": "alinta-energy-assistant",
        "version": "1.0.0"
    }
