import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes.dashboard_api import router as dashboard_router
from routes.twilio_webhook import router as twilio_router

app = FastAPI(title="Amrit Vaayu dMRV API", version="1.0.0")

# Enable CORS for Vite default port
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🚨 NEW: Create local media directory and mount it as a static route
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include the dashboard API routes
app.include_router(dashboard_router, prefix="/api/dashboard")
# Include the Twilio logic routes
app.include_router(twilio_router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Welcome to the Amrit Vaayu dMRV backend!"}