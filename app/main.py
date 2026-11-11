import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to database if URL is provided
    if getattr(settings, "DATABASE_URL", None):
        try:
            logger.info("Initializing Supabase database connection...")
            await init_db(settings.DATABASE_URL)
        except Exception as e:
            logger.error("Failed to connect to Supabase database during startup: %s", e)
    else:
        logger.warning("DATABASE_URL is not set. Database connection skipped.")
    yield
    # Shutdown: close DB connection pool
    await close_db()


app = FastAPI(
    title=getattr(settings, "PROJECT_NAME", "Appointment & Booking API"),
    lifespan=lifespan,
)

# CORS Middleware
origins = getattr(settings, "ALLOWED_ORIGINS", ["*"]) or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Include API v1 Routers
app.include_router(api_v1_router)


@app.get("/")
def read_root():
    return {
        "message": "Appointment & Booking API is running",
        "app_env": getattr(settings, "APP_ENV", "development"),
        "database_configured": bool(getattr(settings, "DATABASE_URL", None)),
        "docs_url": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint to test connection to Supabase database."""
    status_data = {
        "status": "healthy",
        "database": "not_configured",
    }

    if getattr(settings, "DATABASE_URL", None):
        try:
            from app.core.database import _engine
            if _engine is not None:
                async with _engine.connect() as conn:
                    result = await conn.execute(text("SELECT 1"))
                    if result.scalar() == 1:
                        status_data["database"] = "connected"
            else:
                status_data["database"] = "disconnected"
        except Exception as e:
            status_data["database"] = f"error: {str(e)}"
            status_data["status"] = "degraded"

    return status_data
