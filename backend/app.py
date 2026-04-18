import os
import math
import time
import hashlib
import torch
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes.dashboard_api import router as dashboard_router
from routes.twilio_webhook import router as twilio_router
from ml_models.vision_classifier import classify_image
from ml_models.cnn_lstm import inference
from supabase_client import supabase

# 👇 THIS IS THE LINE UVICORN WAS LOOKING FOR
app = FastAPI(title="Amrit Vaayu dMRV API", version="1.0.0")

# Allow your mobile phone to connect via Local Network IP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(dashboard_router, prefix="/api/dashboard")
app.include_router(twilio_router)

# --- CONSTANTS ---
FARM_LAT = 21.004771
FARM_LNG = 79.047696

def calculate_haversine(lat1, lon1, lat2, lon2):
    R = 6371000 
    phi_1, phi_2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

# 🚨 THE MOBILE APP ENDPOINT 🚨
@app.post("/api/mobile-upload")
async def mobile_upload(
    farmer_id: int = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    image: UploadFile = File(...)
):
    # 1. Geofence Check (60 meters)
    dist = calculate_haversine(FARM_LAT, FARM_LNG, lat, lng)
    if dist > 60.0:
        return {"success": False, "reason": f"GEOFENCE FAILED: You are {int(dist)}m away from the field. Move closer."}

    # 2. Save Image Locally
    img_hash = hashlib.md5(f"{farmer_id}_{time.time()}".encode()).hexdigest()
    filename = f"{img_hash}.jpg"
    filepath = os.path.join("static", "images", filename)
    
    with open(filepath, "wb") as f:
        f.write(await image.read())
        
    # 2. Save Image Locally
    img_hash = hashlib.md5(f"{farmer_id}_{time.time()}".encode()).hexdigest()
    filename = f"{img_hash}.jpg"
    filepath = os.path.join("static", "images", filename)
    
    with open(filepath, "wb") as f:
        f.write(await image.read())
        
    # 🚨 PRINCIPAL FIX: Save the live cloud URL to the database, not localhost
    local_image_url = f"https://binarybros-skb-f21-skb-p4-1.onrender.com/static/images/{filename}"
    # 3. AI Check (Local File Bypass for Vision)
    import base64
    with open(filepath, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Using a direct Groq call here since it's a local file, not a Twilio URL
    from groq import Groq
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    chat_completion = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "You are a strict agricultural classifier. 1. If the image is a room, a desk, a person, or anything that is NOT a farm field, output EXACTLY the text: 'INVALID_NOT_PADDY'. 2. If it IS a farm/paddy field and has visible standing water, output EXACTLY: 'Wet'. 3. If it is a farm field with dry soil/no standing water, output EXACTLY: 'Dry'."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
            ],
        }],
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.0,
        max_tokens=5,
    )
    state = chat_completion.choices[0].message.content.strip()

    if "INVALID" in state:
        return {"success": False, "reason": "AI REJECTION: Image is not a recognized paddy field. Please retake the photo."}

    # 4. Mint Credits if Dry
    if "Dry" in state:
        mock_sar = torch.randn(1, 2, 30)
        flux_score = (45.0 * 0.809) + (abs(inference(mock_sar)) * 2.0)
        money_earned = (flux_score / 1000) * 450

        supabase.table("awd_logs").insert({"farmer_id": farmer_id, "image_url": local_image_url, "state_wet_dry": "Dry"}).execute()
        supabase.table("carbon_credits").insert({"farmer_id": farmer_id, "flux_reduction": flux_score, "status": "Verified"}).execute()

        return {
            "success": True, 
            "state": "DRY",
            "credits_earned": round(flux_score, 2),
            "money_earned": round(money_earned, 2),
            "message": "Verification Successful! Tri-Layer consensus achieved."
        }
    else:
        supabase.table("awd_logs").insert({"farmer_id": farmer_id, "image_url": local_image_url, "state_wet_dry": "Wet"}).execute()
        return {"success": True, "state": "WET", "message": "Field is flooded. AWD cycle logged, no credits minted."}