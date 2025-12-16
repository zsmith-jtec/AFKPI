"""AFKPI - Weekly Manufacturing KPI Application.

FastAPI application entry point.
"""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.api import auth, revenue, margin, labor, drill, audit, weeks, upload

# Template and static file paths
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


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
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# HTML Routes
@app.get("/", tags=["Pages"])
def home(request: Request):
    """Redirect to login or dashboard."""
    return RedirectResponse(url="/login")


@app.get("/login", tags=["Pages"])
def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", tags=["Pages"])
def dashboard_page(request: Request):
    """Dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/upload", tags=["Pages"])
def upload_page(request: Request):
    """Upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/api/health", tags=["Health"])
def health_check():
    """API health check."""
    return {"status": "healthy"}
