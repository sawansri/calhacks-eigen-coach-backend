from question_bank.qb import initialize_database
from api import app as api_app

# Expose FastAPI app for: python -m uvicorn main:app --reload
app = api_app

@app.on_event("startup")
async def on_startup():
    """Initialize external services (e.g., MySQL) when the server starts."""
    try:
        print("\n[startup] Initializing Database...")
        initialize_database()
        print("[startup] Database initialization complete.")
    except Exception as e:
        # Non-fatal: API can still serve endpoints that don't hit MySQL
        print(f"[startup] Database initialization error: {e}")