import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from routers import auth, jobs, applications
from config import settings

app = FastAPI(
    title="Job Finders Sierra Leone",
    description="A secure, scalable, and professional-grade REST API for youth employment listings, aligned with SDG 8.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for platform-independent browser clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload storage directory is created
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Safely serve upload static resources
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include modular API routers
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(applications.router)

@app.on_event("startup")
async def startup_event():
    """Lifecycle event handler that creates database tables asynchronously on application startup."""
    async with engine.begin() as conn:
        # Create all tables defined in models.py
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health", tags=["Root"])
async def health():
    """Standard health check and landing route."""
    return {
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "documentation_url": "/docs",
        "status": "healthy"
    }

from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root access directly to Swagger UI docs."""
    return RedirectResponse(url="/docs")


