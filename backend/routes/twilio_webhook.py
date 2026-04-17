"""
=============================================================================
Amrit Vaayu dMRV — Twilio WhatsApp Webhook & Grok LLM Reasoning
=============================================================================
Handles incoming WhatsApp messages from farmers via Twilio's webhook
system. Implements two core flows:

  1. MEDIA/LOCATION FLOW:
     - Farmer sends a paddy field photo via WhatsApp
     - The vision classifier (mock) analyzes the image → "Wet" or "Dry"
     - The AWD cycle observation is logged to Supabase
     - A confirmation message is sent back to the farmer

  2. TEXT QUERY FLOW:
     - Farmer asks a natural language question (e.g., "How many credits?")
     - The query is sent to Grok 7B LLM via the Groq API
     - The LLM receives the farmer's database context for grounded answers
     - A localized, natural language response is returned via TwiML

Author: Binary Bros (Vedant Shivarkar & Akshad Kolawar)
=============================================================================
"""

import os
import sys
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import Response

# ---------------------------------------------------------------------------
# Twilio TwiML helper for constructing WhatsApp responses
# ---------------------------------------------------------------------------
try:
    from twilio.twiml.messaging_response import MessagingResponse
except ImportError:
    MessagingResponse = None
    print("[WARN] twilio package not installed. TwiML responses will use raw XML.")

# ---------------------------------------------------------------------------
# Groq SDK for Grok LLM API calls
# ---------------------------------------------------------------------------
try:
    from groq import Groq
except ImportError:
    Groq = None
    print("[WARN] groq package not installed. LLM reasoning will use fallback responses.")

# ---------------------------------------------------------------------------
# Internal imports
# ---------------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase
from ml_models.vision_classifier import classify_image

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------
GROQ_API_KEY: Optional[str] = os.environ.get("GROQ_API_KEY")

# Initialize Groq client if API key is available
groq_client = None
if Groq and GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("[OK] Groq LLM client initialized.")
else:
    print("[WARN] Groq LLM client not initialized. Check GROQ_API_KEY in .env")

# ---------------------------------------------------------------------------
# Router instance — mounted in app.py under the /api prefix
# ---------------------------------------------------------------------------
router = APIRouter()


# ===========================================================================
# HELPER FUNCTIONS
# ===========================================================================

def _build_twiml_response(message: str) -> Response:
    """
    Constructs a TwiML XML response for Twilio to deliver via WhatsApp.
    Falls back to raw XML if the Twilio SDK is unavailable.
    """
    if MessagingResponse:
        resp = MessagingResponse()
        resp.message(message)
        return Response(content=str(resp), media_type="application/xml")
    else:
        # Fallback: manually construct TwiML XML
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f"<Message>{message}</Message>"
            "</Response>"
        )
        return Response(content=xml, media_type="application/xml")


def _get_or_create_farmer(phone: str) -> dict:
    """
    Look up a farmer by phone number. If not found, create a new record
    with default coordinates (will be updated when location is shared).
    Returns the farmer dict.
    """
    if supabase is None:
        return {"id": 0, "phone": phone, "name": "Unknown"}

    # Try to find existing farmer
    resp = supabase.table("Farmers").select("*").eq("phone", phone).execute()

    if resp.data and len(resp.data) > 0:
        return resp.data[0]

    # Auto-register new farmer with default location (Maharashtra center)
    new_farmer = supabase.table("Farmers").insert({
        "phone": phone,
        "name": "New Farmer",
        "lat": 19.7515,   # Default: Maharashtra center
        "lng": 75.7139,
        "region": "Auto-registered",
    }).execute()

    if new_farmer.data:
        print(f"[INFO] Auto-registered new farmer: {phone}")
        return new_farmer.data[0]

    return {"id": 0, "phone": phone, "name": "Unknown"}


def _fetch_farmer_context(farmer_id: int) -> str:
    """
    Build a textual context string about the farmer's data for the LLM.
    Includes their AWD logs and carbon credit summary so the LLM can
    provide grounded, factual answers.
    """
    if supabase is None:
        return "No database context available."

    context_parts = []

    # Fetch recent AWD logs
    logs = supabase.table("AWD_Logs") \
        .select("state_wet_dry, confidence, timestamp") \
        .eq("farmer_id", farmer_id) \
        .order("timestamp", desc=True) \
        .limit(10) \
        .execute()

    if logs.data:
        context_parts.append(f"Recent AWD observations ({len(logs.data)} records):")
        for log in logs.data:
            context_parts.append(
                f"  - {log['state_wet_dry']} (confidence: {log['confidence']:.0%}) "
                f"on {log['timestamp']}"
            )
    else:
        context_parts.append("No AWD observations recorded yet.")

    # Fetch carbon credits
    credits = supabase.table("Carbon_Credits") \
        .select("flux_reduction, credits_earned, status, methodology") \
        .eq("farmer_id", farmer_id) \
        .execute()

    if credits.data:
        total_credits = sum(c.get("credits_earned", 0) for c in credits.data)
        total_flux = sum(c.get("flux_reduction", 0) for c in credits.data)
        context_parts.append(f"\nCarbon credit summary:")
        context_parts.append(f"  - Total credits earned: {total_credits:.2f}")
        context_parts.append(f"  - Total CH4 flux reduction: {total_flux:.2f} kg CO₂e")
        context_parts.append(f"  - Number of credit records: {len(credits.data)}")
        for c in credits.data:
            context_parts.append(
                f"  - {c['flux_reduction']:.2f} kg reduction → "
                f"{c['credits_earned']:.2f} credits ({c['status']})"
            )
    else:
        context_parts.append("No carbon credits earned yet.")

    return "\n".join(context_parts)


async def _query_grok_llm(user_query: str, farmer_context: str, farmer_name: str) -> str:
    """
    Send the farmer's query and database context to the Grok LLM via Groq API.
    Returns the LLM's natural language response.

    Falls back to a template response if the Groq client is unavailable.
    """
    if groq_client is None:
        # Fallback response when LLM is not configured
        return (
            f"🌾 Namaste {farmer_name}!\n\n"
            f"Your query: \"{user_query}\"\n\n"
            f"📊 Here's what I know:\n{farmer_context}\n\n"
            "⚠️ AI assistant is currently offline. "
            "Please contact your local coordinator for detailed help."
        )

    # Build the system prompt for agricultural context
    system_prompt = (
        "You are 'Amrit Vaayu', a helpful AI assistant for Indian rice paddy farmers "
        "participating in the Alternate Wetting and Drying (AWD) carbon credit program. "
        "You help farmers understand their carbon credits, AWD practices, and methane "
        "reduction efforts. Respond in simple, clear language. If the farmer's message "
        "is in Hindi or Marathi, respond in the same language using Roman script. "
        "Keep responses concise (under 300 characters for WhatsApp readability). "
        "Use relevant emojis to make messages friendly.\n\n"
        f"FARMER DATA CONTEXT:\n{farmer_context}"
    )

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
            model="llama-3.3-70b-versatile",  # Groq-hosted LLM
            temperature=0.6,
            max_tokens=300,
            top_p=0.9,
        )

        return chat_completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"[ERROR] Groq API call failed: {e}")
        return (
            f"🌾 Namaste {farmer_name}! I'm having trouble connecting to my "
            f"AI brain right now. Please try again in a moment. 🙏"
        )


# ===========================================================================
# MAIN WEBHOOK ENDPOINT
# ===========================================================================

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Twilio WhatsApp incoming message webhook handler.

    Twilio sends POST requests with form data containing:
      - Body: Text message content
      - From: Sender's WhatsApp number (whatsapp:+91XXXXXXXXXX)
      - NumMedia: Number of media attachments (0 if text-only)
      - MediaUrl0: URL of the first media attachment (if present)
      - MediaContentType0: MIME type of the first attachment
      - Latitude/Longitude: Location data (if shared)

    Flow:
      1. Parse the incoming message type (media, location, or text)
      2. For media → classify via vision model, log to Supabase
      3. For text  → query Grok LLM with farmer context
      4. Return TwiML response for Twilio to deliver
    """

    # Parse Twilio form data
    form_data = await request.form()

    # Extract key fields from Twilio payload
    body: str = form_data.get("Body", "").strip()
    from_number: str = form_data.get("From", "").replace("whatsapp:", "")
    num_media: int = int(form_data.get("NumMedia", 0))
    media_url: Optional[str] = form_data.get("MediaUrl0")
    media_type: Optional[str] = form_data.get("MediaContentType0")
    latitude: Optional[str] = form_data.get("Latitude")
    longitude: Optional[str] = form_data.get("Longitude")

    print(f"[WEBHOOK] From: {from_number} | Media: {num_media} | Body: {body[:50]}")

    # -----------------------------------------------------------------------
    # Step 1: Identify or register the farmer
    # -----------------------------------------------------------------------
    farmer = _get_or_create_farmer(from_number)
    farmer_id = farmer.get("id", 0)
    farmer_name = farmer.get("name", "Farmer")

    # -----------------------------------------------------------------------
    # Step 2: Handle LOCATION sharing — update farmer coordinates
    # -----------------------------------------------------------------------
    if latitude and longitude:
        try:
            lat_val = float(latitude)
            lng_val = float(longitude)

            if supabase:
                supabase.table("Farmers").update({
                    "lat": lat_val,
                    "lng": lng_val,
                }).eq("id", farmer_id).execute()

                print(f"[INFO] Updated location for farmer {farmer_id}: ({lat_val}, {lng_val})")

            return _build_twiml_response(
                f"📍 Location updated! Lat: {lat_val:.4f}, Lng: {lng_val:.4f}\n"
                f"Your field is now mapped on the Amrit Vaayu dashboard. 🗺️"
            )

        except (ValueError, TypeError) as e:
            print(f"[ERROR] Invalid location data: {e}")

    # -----------------------------------------------------------------------
    # Step 3: Handle MEDIA (image) — classify and log AWD observation
    # -----------------------------------------------------------------------
    if num_media > 0 and media_url:
        # Run the vision classifier (mock in development)
        classification = classify_image(media_url)
        state = classification["state"]         # "Wet" or "Dry"
        confidence = classification["confidence"]

        # Log the AWD observation to Supabase
        if supabase and farmer_id:
            supabase.table("AWD_Logs").insert({
                "farmer_id": farmer_id,
                "image_url": media_url,
                "state_wet_dry": state,
                "confidence": confidence,
            }).execute()

            print(f"[INFO] AWD log created: farmer={farmer_id}, state={state}, conf={confidence:.2f}")

        # Determine emoji and message based on state
        if state == "Wet":
            emoji = "💧"
            advice = "Your field is in the WETTING phase. Maintain water level for optimal CH4 reduction."
        else:
            emoji = "🏜️"
            advice = "Your field is in the DRYING phase. Good AWD practice! This reduces methane emissions."

        return _build_twiml_response(
            f"{emoji} Field Status: *{state}* (Confidence: {confidence:.0%})\n\n"
            f"📋 {advice}\n\n"
            f"✅ Observation logged to your Amrit Vaayu record."
        )

    # -----------------------------------------------------------------------
    # Step 4: Handle TEXT query — pass to Grok LLM with context
    # -----------------------------------------------------------------------
    if body:
        # Fetch farmer's database context for grounded LLM responses
        farmer_context = _fetch_farmer_context(farmer_id)

        # Query the LLM
        llm_response = await _query_grok_llm(body, farmer_context, farmer_name)

        return _build_twiml_response(llm_response)

    # -----------------------------------------------------------------------
    # Fallback: Empty message
    # -----------------------------------------------------------------------
    return _build_twiml_response(
        "🌾 Namaste! Welcome to Amrit Vaayu.\n\n"
        "Send me:\n"
        "📸 A photo of your paddy field\n"
        "📍 Your location\n"
        "💬 Any question about your carbon credits\n\n"
        "— Amrit Vaayu dMRV 🌍"
    )


# ===========================================================================
# WEBHOOK STATUS ENDPOINT (for Twilio configuration verification)
# ===========================================================================

@router.get("/whatsapp/status")
async def whatsapp_status():
    """
    Simple GET endpoint to verify the webhook is reachable.
    Useful when configuring the Twilio WhatsApp sandbox URL.
    """
    return {
        "status": "ok",
        "webhook": "/api/whatsapp",
        "method": "POST",
        "description": "Amrit Vaayu dMRV WhatsApp webhook is active.",
        "llm_available": groq_client is not None,
        "supabase_available": supabase is not None,
    }
