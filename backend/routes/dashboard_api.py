from fastapi import APIRouter, HTTPException
from supabase_client import supabase

# Router for dashboard data, prefix is handled in app.py
router = APIRouter(tags=["dashboard"])

@router.get("/farmers")
def get_farmers():
    """
    Fetch all farmers and the total count from Supabase.
    """
    try:
        response = supabase.table("Farmers").select("*").execute()
        return {"total_farmers": len(response.data), "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/awd-logs")
def get_recent_awd_logs():
    """
    Fetch recent Alternate Wetting and Drying (AWD) cycle logs.
    Ordered by the most recent timestamp.
    """
    try:
        response = supabase.table("AWD_Logs").select("*, Farmers(phone)").order("timestamp", desc=True).limit(50).execute()
        return {"logs": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/carbon-credits")
def get_aggregated_carbon_credits():
    """
    Fetch and aggregate the total carbon credits (flux reduction).
    """
    try:
        response = supabase.table("Carbon_Credits").select("*").execute()
        total_flux_reduction = sum([item.get('flux_reduction', 0) for item in response.data])
        return {"total_flux_reduction": total_flux_reduction, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
