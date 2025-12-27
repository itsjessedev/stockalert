"""Main FastAPI application"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api import inventory_router, alerts_router, locations_router
from .scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting StockAlert application")
    logger.info(f"Demo mode: {settings.demo_mode}")

    # Start background scheduler
    start_scheduler()

    yield

    # Shutdown
    logger.info("Shutting down StockAlert application")
    stop_scheduler()


app = FastAPI(
    title="StockAlert",
    description="Real-time inventory monitoring with smart reorder alerts",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(inventory_router)
app.include_router(alerts_router)
app.include_router(locations_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "StockAlert",
        "version": "1.0.0",
        "description": "Inventory Monitoring System",
        "demo_mode": settings.demo_mode,
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": logging.Formatter().formatTime(logging.LogRecord("", 0, "", 0, "", (), None)),
        "demo_mode": settings.demo_mode,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
