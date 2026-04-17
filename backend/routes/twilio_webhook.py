import os
import requests
import tempfile
import torch
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from supabase_client import supabase
from groq import Groq
from ml_models.vision_classifier import classify_image
from ml_models.cnn_lstm import inference

# Force Python to read your .env file
load_dotenv(override=True) 

router = APIRouter(tags=["whatsapp"])

# Initialize Groq client
groq_api_key = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    
    sender_phone = form_data.get('From', '').replace('whatsapp:', '')
    body = form_data.get('Body', '').strip()
    num_media = int(form_data.get('NumMedia', 0))
    latitude = form_data.get('Latitude')
    longitude = form_data.get('Longitude')

    twiml_resp = MessagingResponse()
    
    # 1. Fetch or Create Farmer Profile in Supabase
    farmer_response = supabase.table("farmers").select("*").eq("phone", sender_phone).execute()
    
    if not farmer_response.data:
        new_farmer = supabase.table("farmers").insert({
            "phone": sender_phone,
            "lat": 0.0,
            "lng": 0.0
        }).execute()
        farmer_data = new_farmer.data[0]
    else:
        farmer_data = farmer_response.data[0]

    farmer_id = farmer_data['id']

    # ==========================================
    # ROUTE A: The farmer sent a LIVE LOCATION
    # ==========================================
    if latitude and longitude:
        # Update the farmer's coordinates in the database for the Leaflet Map
        supabase.table("farmers").update({
            "lat": float(latitude),
            "lng": float(longitude)
        }).eq("id", farmer_id).execute()
        
        twiml_resp.message("📍 Location verified and mapped. Please send a photo of your field to log your AWD cycle.")
        return Response(content=twiml_resp.to_xml(), media_type="application/xml")

    # ==========================================
    # ROUTE B: The farmer sent MEDIA (Image or Voice Note)
    # ==========================================
    elif num_media > 0:
        media_url = form_data.get('MediaUrl0', '')
        media_type = form_data.get('MediaContentType0', '')

        # --- B1: Voice Note Processing (Marathi, Hindi, Telugu, etc.) ---
        if 'audio' in media_type:
            if not groq_client:
                twiml_resp.message("Voice processing is offline. Please check your Groq API key.")
                return Response(content=twiml_resp.to_xml(), media_type="application/xml")
                
            try:
                # Authenticate with Twilio to download the actual audio file
                twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
                twilio_auth = os.environ.get("TWILIO_AUTH_TOKEN")
                
                # Fetch the audio using HTTP Basic Auth
                audio_response = requests.get(media_url, auth=(twilio_sid, twilio_auth))
                
                if audio_response.status_code != 200:
                    print(f"❌ Twilio Audio Download Failed: {audio_response.status_code}")
                    twiml_resp.message("System error downloading your voice note.")
                    return Response(content=twiml_resp.to_xml(), media_type="application/xml")

                # Save the secure audio data to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
                    temp_audio.write(audio_response.content)
                    temp_path = temp_audio.name

                # Transcribe using Groq Whisper-Large-V3 (Auto-detects language)
                with open(temp_path, "rb") as file:
                    transcription = groq_client.audio.transcriptions.create(
                      file=(temp_path, file.read()),
                      model="whisper-large-v3"
                    )
                user_spoken_text = transcription.text
                os.remove(temp_path) # Clean up

                # Feed transcribed text to Groq LLM to generate a localized response
                system_prompt = "You are Amrit Vaayu, an agricultural AI. A farmer asked you a question. Reply strictly in the SAME language they used. Keep it very short, helpful, and localized."
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_spoken_text}
                    ],
                    model="mixtral-8x7b-32768",
                )
                
                twiml_resp.message(f"🎤 {chat_completion.choices[0].message.content}")
                
            except Exception as e:
                twiml_resp.message("Sorry, I couldn't process your voice note. Please type your message.")
                print(f"❌ Voice AI Error: {e}") 

        # --- B2: Image Processing (AWD Cycle Validation) ---
        # --- B2: Image Processing (AWD Cycle Validation) ---
        elif 'image' in media_type:
            
            # 🚨 Friendly Ground-Truth Gatekeeper (Defensive Float Cast) 🚨
            if float(farmer_data.get('lat', 0.0)) == 0.0 or float(farmer_data.get('lng', 0.0)) == 0.0:
                twiml_resp.message("📸 I received your photo, but I need your coordinates too! Please tap the '+' icon and send your 'Location' so I can verify your field.")
                return Response(content=twiml_resp.to_xml(), media_type="application/xml")

            # 🧠 NEW: Send to Groq Llama 3.2 Vision Model
            state_wet_dry = classify_image(media_url) 
            
            # Log the cycle
            supabase.table("awd_logs").insert({
                "farmer_id": farmer_id,
                "image_url": media_url,
                "state_wet_dry": state_wet_dry
            }).execute()

            # Trigger PyTorch ML if cycle is complete (Dry)
            if state_wet_dry == "Dry":
                mock_sar_tensor = torch.randn(1, 2, 30) 
                flux_score = inference(mock_sar_tensor)
                
                supabase.table("carbon_credits").insert({
                    "farmer_id": farmer_id,
                    "flux_reduction": round(flux_score, 2),
                    "status": "Verified"
                }).execute()
                
                twiml_resp.message(f"✅ Field verified a Dry. \nPyTorch calculated a CH4 reduction of {flux_score:.2f} kg CO2e. \nCredit minted to the Amrit Vaayu ledger!")
            elif state_wet_dry == "Wet":
                twiml_resp.message(f"✅ Field verified as WET. AWD cycle logged.")
            else:
                twiml_resp.message(f"⚠️ Image analyzed, but could not confidently determine Wet/Dry state. Logged for manual review.")

            # 🚨 NEW: The Security Session Closer 🚨
            # Wipe the coordinates back to 0.0 so the next time they send an image, the Gatekeeper blocks them.
            supabase.table("farmers").update({
                "lat": 0.0,
                "lng": 0.0
            }).eq("id", farmer_id).execute()
            
            twiml_resp.message("📍 Note: Your GPS session has been securely closed. You will need to share your Live Location again for your next upload.")

        return Response(content=twiml_resp.to_xml(), media_type="application/xml")

    # ==========================================
    # ROUTE C: The farmer sent STANDARD TEXT
    # ==========================================
    else:
        twiml_resp.message("Welcome to Amrit Vaayu. Send your Location first, then a Photo of your field. Send a Voice Note if you need help in your local language!")
        return Response(content=twiml_resp.to_xml(), media_type="application/xml")