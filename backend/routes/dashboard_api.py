from fastapi import APIRouter, HTTPException
from pydantic import BaseModel 
from supabase_client import supabase
import torch
from ml_models.cnn_lstm import inference

router = APIRouter(tags=["dashboard"])

@router.get("/farmers")
def get_farmers():
    try:
        response = supabase.table("farmers").select("*").execute()
        return {"total_farmers": len(response.data), "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/awd-logs")
def get_recent_awd_logs():
    try:
        response = supabase.table("awd_logs").select("*, farmers(phone)").order("timestamp", desc=True).limit(50).execute()
        return {"logs": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/carbon-credits")
def get_aggregated_carbon_credits():
    try:
        response = supabase.table("carbon_credits").select("*").execute()
        total_flux_reduction = sum([item.get('flux_reduction', 0) for item in response.data])
        return {"total_flux_reduction": total_flux_reduction, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🚨 THE SMART EDGE NODE ENDPOINT (WITH TERMINAL LOGS) 🚨
@router.get("/live-esp32")
def get_live_esp32():
    try:
        response = supabase.table("esp32_telemetry").select("*").order("timestamp", desc=True).limit(1).execute()
        if not response.data:
            return {"data": None, "minted_just_now": False}
            
        latest = response.data[0]
        pump_status = latest.get("pump_status", "OFF")
        timestamp_str = latest.get("timestamp")
        
        minted = False
        
        # Auto-Minting Logic
        if pump_status == "ON":
            check = supabase.table("awd_logs").select("*").eq("image_url", f"Hardware_Node_{timestamp_str}").execute()
            
            if not check.data:
                print(f"==================================================")
                print(f"🌿 HARDWARE TRIGGER DETECTED! PUMP IS {pump_status} (DRY)")
                print(f"⚙️ EXECUTING INFERENCE AND MINTING CARBON CREDITS...")
                print(f"==================================================")
                
                mock_sar = torch.randn(1, 2, 30)
                flux_score = (45.0 * 0.809) + (abs(inference(mock_sar)) * 2.0)
                
                # Write to visual ledger
                supabase.table("awd_logs").insert({
                    "farmer_id": 1, 
                    "image_url": f"Hardware_Node_{timestamp_str}", 
                    "state_wet_dry": "Dry"
                }).execute()
                
                # Write to financial ledger
                supabase.table("carbon_credits").insert({
                    "farmer_id": 1, 
                    "flux_reduction": flux_score, 
                    "status": "Hardware Verified"
                }).execute()
                
                minted = True
                
        return {"data": latest, "minted_just_now": minted}
    except Exception as e:
        print(f"❌ Backend Error in live-esp32: {e}")
        return {"data": None, "minted_just_now": False}

class FarmerRegistration(BaseModel):
    name: str
    phone: str
    landSize: float

@router.post("/register")
def register_farmer(farmer: FarmerRegistration):
    try:
        existing = supabase.table("farmers").select("*").eq("phone", farmer.phone).execute()
        if existing.data:
            response = supabase.table("farmers").update({"name": farmer.name, "land_size": farmer.landSize}).eq("phone", farmer.phone).execute()
        else:
            response = supabase.table("farmers").insert({"phone": farmer.phone, "name": farmer.name, "land_size": farmer.landSize, "lat": 0.0, "lng": 0.0}).execute()
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))