import os
from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from supabase_client import supabase
from groq import Groq
from ml_models.vision_classifier import classify_image

router = APIRouter(tags=["whatsapp"])

# Initialize Groq client securely 
groq_api_key = os.environ.get("GROQ_API_KEY", "mock_key")
try:
    groq_client = Groq(api_key=groq_api_key)
except Exception:
    groq_client = None

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Webhook to handle incoming WhatsApp messages from Twilio.
    Parses payload for media/location or query context,
    and returns a TwiML response.
    """
    # Parse x-www-form-urlencoded data provided by Twilio
    form_data = await request.form()
    
    sender_phone = form_data.get('From', '').replace('whatsapp:', '')
    body = form_data.get('Body', '').strip()
    num_media = int(form_data.get('NumMedia', 0))
    latitude = form_data.get('Latitude')
    longitude = form_data.get('Longitude')

    twiml_resp = MessagingResponse()
    
    # Validate or create farmer record
    farmer_response = supabase.table("Farmers").select("*").eq("phone", sender_phone).execute()
    
    if not farmer_response.data:
        # Auto-create skeleton profile if missing for mock hackathon purposes
        new_farmer = supabase.table("Farmers").insert({
            "phone": sender_phone,
            "lat": float(latitude) if latitude else 0.0,
            "lng": float(longitude) if longitude else 0.0
        }).execute()
        farmer_data = new_farmer.data[0]
    else:
        farmer_data = farmer_response.data[0]

    farmer_id = farmer_data['id']

    # Logic Flow Branch 1: Payload contains media/location
    if num_media > 0 or latitude:
        media_url = form_data.get('MediaUrl0', '') if num_media > 0 else None
        
        # Simulate Vision Classifier
        state_wet_dry = classify_image(media_url) if media_url else "Wet" 

        # Insert the AWD cycle log into Supabase
        supabase.table("AWD_Logs").insert({
            "farmer_id": farmer_id,
            "image_url": media_url,
            "state_wet_dry": state_wet_dry
        }).execute()

        twiml_resp.message(f"✅ AWD Log received successfully. Field state identified as: {state_wet_dry}")
        return Response(content=twiml_resp.to_xml(), media_type="application/xml")

    # Logic Flow Branch 2: Text query -> Grok LLM Reasoning
    try:
        # Gather context from DB
        credits_resp = supabase.table("Carbon_Credits").select("*").eq("farmer_id", farmer_id).execute()
        total_creds = sum([c.get('flux_reduction', 0) for c in credits_resp.data])

        system_prompt = (
            f"You are the agricultural AI assistant for Amrit Vaayu dMRV. "
            f"The user is a farmer. Farmer ID is {farmer_id}. "
            f"They currently have {total_creds} aggregated flux reduction credits. "
            f"Answer their questions concisely and in natural, local language."
        )

        if groq_client:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": body}
                ],
                model="mixtral-8x7b-32768", # Valid model for Groq Python SDK placeholder
            )
            reply_text = chat_completion.choices[0].message.content
        else:
            reply_text = f"You currently have {total_creds} carbon credits. Keep up the good work!"
            
        twiml_resp.message(reply_text)

    except Exception as e:
        twiml_resp.message("System is calculating your metrics. Please try again.")

    return Response(content=twiml_resp.to_xml(), media_type="application/xml")
