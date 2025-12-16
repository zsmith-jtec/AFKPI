"""AFKPI - Weekly Manufacturing KPI Application.

FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.api import auth, revenue, margin, labor, drill, audit, weeks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Weekly Manufacturing KPI Dashboard - Track revenue, margin, and labor metrics",
    lifespan=lifespan,
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(weeks.router, prefix="/api/weeks", tags=["Weeks"])
app.include_router(revenue.router, prefix="/api/revenue", tags=["Revenue"])
app.include_router(margin.router, prefix="/api/margin", tags=["Margin"])
app.include_router(labor.router, prefix="/api/labor", tags=["Labor"])
app.include_router(drill.router, prefix="/api/drill", tags=["Drill-Down"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/api/health", tags=["Health"])
def health_check():
    """API health check."""
    return {"status": "healthy"}
