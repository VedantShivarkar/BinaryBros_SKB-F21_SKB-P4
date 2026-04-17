"""
=============================================================================
Amrit Vaayu dMRV — FastAPI Application Entry Point
=============================================================================
Main application file. Initializes the FastAPI instance, configures CORS
middleware, and mounts all API route modules.

Run with:
    uvicorn app:app --reload --port 8000
=============================================================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# Initialize FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Amrit Vaayu dMRV API",
    description=(
        "Cloud-Proof digital Monitoring, Reporting, and Verification "
        "system for carbon markets. Built by Binary Bros."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
# Allow the Vite React dev server (localhost:5173) to call our API.
# In production, restrict `allow_origins` to the actual deployed domain.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite React dev server
        "http://127.0.0.1:5173",  # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],          # Allow all HTTP methods
    allow_headers=["*"],          # Allow all headers
)


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
async def health_check():
    """Root endpoint — confirms the API server is running."""
    return {
        "status": "online",
        "project": "Amrit Vaayu dMRV",
        "team": "Binary Bros",
        "version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# Route Registration (will be populated in Step 2 & 3)
# ---------------------------------------------------------------------------
# from routes.dashboard_api import router as dashboard_router
# from routes.twilio_webhook import router as twilio_router
# app.include_router(dashboard_router, prefix="/api", tags=["Dashboard"])
# app.include_router(twilio_router, prefix="/api", tags=["Twilio"])
