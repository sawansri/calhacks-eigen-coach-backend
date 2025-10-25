"""
Eigen Coach Backend - Main Application Entry Point
Initializes database and exposes FastAPI endpoints.
"""

from api import app as api_app
from database.db import DatabaseManager

# Expose FastAPI app for: python -m uvicorn main:app --reload
app = api_app


@app.on_event("startup")
async def on_startup():
    """Initialize database connection pool when server starts."""
    try:
        print("\n" + "=" * 60)
        print("Eigen Coach Backend Starting")
        print("=" * 60)
        print("\n[Startup] Initializing database connection pool...")
        DatabaseManager.initialize()
        print("[Startup] ✓ Database initialized and ready")
        print("[Startup] ✓ API endpoints available")
        print("\n" + "=" * 60)
        print("Server Ready!")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"\n[Startup] ✗ Database initialization error: {e}")
        import traceback
        traceback.print_exc()
        raise


@app.on_event("shutdown")
async def on_shutdown():
    """Close database connections when server shuts down."""
    try:
        DatabaseManager.close_all()
        print("\n[Shutdown] Database connections closed.")
    except Exception as e:
        print(f"[Shutdown] Error closing databases: {e}")