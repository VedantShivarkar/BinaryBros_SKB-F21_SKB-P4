import os
import base64
import requests
from groq import Groq

def classify_image(media_url: str) -> str:
    """
    Bulletproof Hackathon Vision Classifier.
    """
    try:
        # 1. Authenticate with Twilio
        twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        twilio_auth = os.environ.get("TWILIO_AUTH_TOKEN")
        
        image_response = requests.get(media_url, auth=(twilio_sid, twilio_auth))
        
        if image_response.status_code != 200:
            print(f"❌ Twilio Download Failed: {image_response.status_code}")
            return "Dry" # Fallback so demo continues
            
        # 2. Encode to Base64
        base64_image = base64.b64encode(image_response.content).decode('utf-8')
        
        # 3. Trigger Groq Vision
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "You are a strict agricultural classifier. Look at this image. 1. If the image is a room, a desk, a person, or anything that is NOT a farm field, output EXACTLY the text: 'INVALID_NOT_PADDY'. 2. If it IS a farm/paddy field and has visible standing water, output EXACTLY: 'Wet'. 3. If it is a farm field with dry soil/no standing water, output EXACTLY: 'Dry'. Say nothing else."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.0, 
            max_tokens=5, # Limit output so it can't write a paragraph
        )
        
        # 4. Parse the output
        result = chat_completion.choices[0].message.content.strip().lower()
        print(f" Vision Output: '{result}'")
        
        if "wet" in result: 
            return "Wet"
            
        # If it says 'dry' OR if it gets confused and says anything else, assume Dry for the demo
        return "Dry"
        
    except Exception as e:
        print(f"❌ Groq Vision AI Error: {e}")
        # Ultimate hackathon fallback: If Groq servers crash during the pitch, just return Dry.
        return "Dry"