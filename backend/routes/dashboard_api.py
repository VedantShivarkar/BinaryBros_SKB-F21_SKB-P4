"""
=============================================================================
Amrit Vaayu dMRV — Dashboard API Routes
=============================================================================
Serves data to the React frontend by querying the Supabase PostgreSQL
instance. Provides endpoints for:

  • Farmer CRUD and geospatial data (for Leaflet map)
  • AWD cycle log retrieval and insertion
  • Carbon credit aggregation and status tracking
  • Dashboard summary statistics

All responses follow a consistent JSON envelope:
    { "status": "ok", "data": ... }
    { "status": "error", "detail": "..." }

Author: Binary Bros (Vedant Shivarkar & Akshad Kolawar)
=============================================================================
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Import the singleton Supabase client
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase

# ---------------------------------------------------------------------------
# Router instance — mounted in app.py under the /api prefix
# ---------------------------------------------------------------------------
router = APIRouter()


# ===========================================================================
# PYDANTIC MODELS — Request/Response validation
# ===========================================================================

class FarmerCreate(BaseModel):
    """Schema for registering a new farmer."""
    phone: str = Field(..., description="E.164 phone number, e.g. +919876543210")
    name: str = Field(default="Unknown", description="Farmer display name")
    lat: float = Field(..., ge=-90, le=90, description="Latitude (WGS84)")
    lng: float = Field(..., ge=-180, le=180, description="Longitude (WGS84)")
    region: str = Field(default="Unassigned", description="Administrative region")


class AWDLogCreate(BaseModel):
    """Schema for inserting a new AWD observation log."""
    farmer_id: int = Field(..., description="Foreign key to Farmers table")
    image_url: Optional[str] = Field(None, description="Twilio media URL")
    state_wet_dry: str = Field(..., pattern="^(Wet|Dry)$", description="Classified state")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Model confidence")


class CarbonCreditCreate(BaseModel):
    """Schema for inserting a new carbon credit record."""
    farmer_id: int = Field(..., description="Foreign key to Farmers table")
    flux_reduction: float = Field(..., ge=0.0, description="CH4 reduction in kg CO₂e")
    credits_earned: float = Field(default=0.0, ge=0.0, description="Tokenized credit value")
    status: str = Field(default="Pending", pattern="^(Pending|Verified|Issued|Retired)$")
    methodology: str = Field(default="AMS-III.AU", description="CDM methodology reference")


# ===========================================================================
# HELPER — Validate Supabase client is available
# ===========================================================================

def _require_supabase():
    """Raises HTTP 503 if the Supabase client failed to initialize."""
    if supabase is None:
        raise HTTPException(
            status_code=503,
            detail="Supabase client is not initialized. Check server logs for SUPABASE_URL/SUPABASE_KEY."
        )


# ===========================================================================
# DASHBOARD SUMMARY — Aggregated metrics for the Level 1 dashboard
# ===========================================================================

@router.get("/dashboard/summary")
async def get_dashboard_summary():
    """
    Returns high-level summary statistics for the dashboard header cards:
      - Total registered farmers
      - Total AWD observations logged
      - Total carbon credits issued
      - Breakdown of credit statuses
    """
    _require_supabase()

    try:
        # --- Total farmers ---
        farmers_resp = supabase.table("Farmers").select("id", count="exact").execute()
        total_farmers = farmers_resp.count if farmers_resp.count is not None else 0

        # --- Total AWD logs ---
        logs_resp = supabase.table("AWD_Logs").select("id", count="exact").execute()
        total_logs = logs_resp.count if logs_resp.count is not None else 0

        # --- Carbon credit aggregation ---
        credits_resp = supabase.table("Carbon_Credits").select("*").execute()
        credits_data = credits_resp.data or []

        total_flux_reduction = sum(c.get("flux_reduction", 0) for c in credits_data)
        total_credits_earned = sum(c.get("credits_earned", 0) for c in credits_data)

        # Status breakdown
        status_counts = {}
        for c in credits_data:
            status = c.get("status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "status": "ok",
            "data": {
                "total_farmers": total_farmers,
                "total_awd_logs": total_logs,
                "total_flux_reduction_kg": round(total_flux_reduction, 2),
                "total_credits_earned": round(total_credits_earned, 2),
                "credit_status_breakdown": status_counts,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard summary query failed: {str(e)}")


# ===========================================================================
# FARMERS — CRUD Endpoints
# ===========================================================================

@router.get("/farmers")
async def get_all_farmers():
    """
    Fetch all registered farmers with their geolocation data.
    Used by the Level 2 Leaflet map to plot farmer coordinates.
    """
    _require_supabase()

    try:
        response = supabase.table("Farmers").select("*").order("created_at", desc=True).execute()
        return {"status": "ok", "data": response.data or []}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch farmers: {str(e)}")


@router.get("/farmers/{farmer_id}")
async def get_farmer_by_id(farmer_id: int):
    """Fetch a single farmer by their ID."""
    _require_supabase()

    try:
        response = supabase.table("Farmers").select("*").eq("id", farmer_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail=f"Farmer with id={farmer_id} not found.")

        return {"status": "ok", "data": response.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch farmer: {str(e)}")


@router.post("/farmers", status_code=201)
async def create_farmer(farmer: FarmerCreate):
    """
    Register a new farmer. Phone number must be unique (E.164 format).
    Returns the newly created farmer record.
    """
    _require_supabase()

    try:
        response = supabase.table("Farmers").insert({
            "phone": farmer.phone,
            "name": farmer.name,
            "lat": farmer.lat,
            "lng": farmer.lng,
            "region": farmer.region,
        }).execute()

        return {"status": "ok", "data": response.data[0] if response.data else None}

    except Exception as e:
        # Catch unique constraint violations on phone
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail=f"Farmer with phone {farmer.phone} already exists.")
        raise HTTPException(status_code=500, detail=f"Failed to create farmer: {str(e)}")


# ===========================================================================
# AWD LOGS — Alternate Wetting & Drying Observations
# ===========================================================================

@router.get("/awd-logs")
async def get_awd_logs(
    limit: int = Query(default=50, ge=1, le=500, description="Max records to return"),
    farmer_id: Optional[int] = Query(default=None, description="Filter by farmer ID"),
):
    """
    Fetch recent AWD observation logs, optionally filtered by farmer_id.
    Joins farmer name for display convenience. Ordered by most recent first.
    """
    _require_supabase()

    try:
        query = supabase.table("AWD_Logs").select(
            "*, Farmers(name, phone, region)"
        ).order("timestamp", desc=True).limit(limit)

        # Apply optional farmer filter
        if farmer_id is not None:
            query = query.eq("farmer_id", farmer_id)

        response = query.execute()
        return {"status": "ok", "data": response.data or []}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch AWD logs: {str(e)}")


@router.post("/awd-logs", status_code=201)
async def create_awd_log(log: AWDLogCreate):
    """
    Insert a new AWD cycle observation. Typically called after the
    vision classifier processes a WhatsApp image submission.
    """
    _require_supabase()

    try:
        # Verify farmer exists
        farmer_check = supabase.table("Farmers").select("id").eq("id", log.farmer_id).execute()
        if not farmer_check.data:
            raise HTTPException(status_code=404, detail=f"Farmer with id={log.farmer_id} not found.")

        response = supabase.table("AWD_Logs").insert({
            "farmer_id": log.farmer_id,
            "image_url": log.image_url,
            "state_wet_dry": log.state_wet_dry,
            "confidence": log.confidence,
        }).execute()

        return {"status": "ok", "data": response.data[0] if response.data else None}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create AWD log: {str(e)}")


# ===========================================================================
# CARBON CREDITS — Methane Flux Reduction Tracking
# ===========================================================================

@router.get("/carbon-credits")
async def get_carbon_credits(
    limit: int = Query(default=50, ge=1, le=500, description="Max records to return"),
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
        description="Filter by status: Pending, Verified, Issued, Retired"
    ),
    farmer_id: Optional[int] = Query(default=None, description="Filter by farmer ID"),
):
    """
    Fetch carbon credit records with optional filtering by status and farmer.
    Joins farmer details for the Level 1 dashboard table.
    """
    _require_supabase()

    try:
        query = supabase.table("Carbon_Credits").select(
            "*, Farmers(name, phone, region)"
        ).order("created_at", desc=True).limit(limit)

        if status_filter:
            query = query.eq("status", status_filter)
        if farmer_id is not None:
            query = query.eq("farmer_id", farmer_id)

        response = query.execute()
        return {"status": "ok", "data": response.data or []}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch carbon credits: {str(e)}")


@router.post("/carbon-credits", status_code=201)
async def create_carbon_credit(credit: CarbonCreditCreate):
    """
    Insert a new carbon credit record after CNN-LSTM model inference.
    """
    _require_supabase()

    try:
        # Verify farmer exists
        farmer_check = supabase.table("Farmers").select("id").eq("id", credit.farmer_id).execute()
        if not farmer_check.data:
            raise HTTPException(status_code=404, detail=f"Farmer with id={credit.farmer_id} not found.")

        response = supabase.table("Carbon_Credits").insert({
            "farmer_id": credit.farmer_id,
            "flux_reduction": credit.flux_reduction,
            "credits_earned": credit.credits_earned,
            "status": credit.status,
            "methodology": credit.methodology,
        }).execute()

        return {"status": "ok", "data": response.data[0] if response.data else None}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create carbon credit: {str(e)}")


@router.patch("/carbon-credits/{credit_id}/status")
async def update_credit_status(credit_id: int, new_status: str = Query(..., alias="status")):
    """
    Update the verification status of a specific carbon credit.
    Status lifecycle: Pending → Verified → Issued → Retired
    """
    _require_supabase()

    valid_statuses = {"Pending", "Verified", "Issued", "Retired"}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{new_status}'. Must be one of: {valid_statuses}"
        )

    try:
        response = supabase.table("Carbon_Credits") \
            .update({"status": new_status}) \
            .eq("id", credit_id) \
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail=f"Carbon credit id={credit_id} not found.")

        return {"status": "ok", "data": response.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update credit status: {str(e)}")


# ===========================================================================
# FARMER MAP DATA — Optimized endpoint for map markers
# ===========================================================================

@router.get("/map/farmers")
async def get_farmer_map_data():
    """
    Returns a lightweight payload optimized for Leaflet map markers.
    Each farmer includes their latest AWD state for color-coded markers
    (Blue = Wet, Brown = Dry).
    """
    _require_supabase()

    try:
        # Fetch all farmers
        farmers_resp = supabase.table("Farmers").select("*").execute()
        farmers = farmers_resp.data or []

        # Fetch the latest AWD log for each farmer
        logs_resp = supabase.table("AWD_Logs") \
            .select("farmer_id, state_wet_dry, confidence, timestamp") \
            .order("timestamp", desc=True) \
            .execute()
        logs = logs_resp.data or []

        # Build a lookup of farmer_id → latest AWD state
        latest_state = {}
        for log in logs:
            fid = log["farmer_id"]
            if fid not in latest_state:
                latest_state[fid] = {
                    "state": log["state_wet_dry"],
                    "confidence": log["confidence"],
                    "last_observed": log["timestamp"],
                }

        # Merge farmer data with their latest state
        map_data = []
        for farmer in farmers:
            fid = farmer["id"]
            state_info = latest_state.get(fid, {})
            map_data.append({
                "id": fid,
                "name": farmer.get("name", "Unknown"),
                "phone": farmer.get("phone"),
                "lat": farmer["lat"],
                "lng": farmer["lng"],
                "region": farmer.get("region", "Unassigned"),
                "latest_state": state_info.get("state", "Unknown"),
                "confidence": state_info.get("confidence", 0.0),
                "last_observed": state_info.get("last_observed"),
            })

        return {"status": "ok", "data": map_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch map data: {str(e)}")
