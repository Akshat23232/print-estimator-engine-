"""
FastAPI Application Entry Point

This is the main application factory and configuration.

Design Decisions:
1. Use lifespan context manager for startup/shutdown (modern FastAPI pattern)
2. Include CORS middleware for frontend integration
3. Centralized exception handling for consistent error responses
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import intake

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Startup: Validate configuration, warm up connections
    Shutdown: Clean up resources
    
    NOTE: In production, add database connection pooling here
    """
    logger.info("Starting Print Estimator API...")
    
    # Validate critical configuration at startup
    # This fails fast if OPENAI_API_KEY is missing
    _ = get_settings()
    logger.info("Configuration validated successfully")
    
    # TODO: Initialize database connection pool
    # TODO: Warm up LLM client connection
    
    yield
    
    # Shutdown
    logger.info("Shutting down Print Estimator API...")
    # TODO: Close database connections
    # TODO: Flush any pending webhooks


app = FastAPI(
    title="Print Estimator API",
    description="AI-driven print specification extraction and pricing engine",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS Configuration
# NOTE: In production, restrict origins to your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for consistent error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler.
    
    Design Decision: Return consistent error format for all unhandled exceptions.
    In production, you'd want to:
    1. Log the full traceback
    2. Send to error monitoring (Sentry, etc.)
    3. Return sanitized message to client
    """
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An internal error occurred",
            "detail": str(exc) if settings.log_level == "DEBUG" else None
        }
    )


# Include routers
app.include_router(intake.router, tags=["intake"])


@app.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.
    
    Returns simple status for load balancers and k8s probes.
    
    TODO: Add deeper health checks:
    - Database connectivity
    - LLM API reachability
    - n8n webhook status
    """
    return {
        "status": "healthy",
        "version": "0.1.0"
    }
