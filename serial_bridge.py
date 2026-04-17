import serial
import json
import time
import os
from supabase import create_client
from dotenv import load_dotenv

# Force load the .env file from the backend folder
load_dotenv(dotenv_path="backend/.env") # Adjust path if your .env is in the root

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ CRITICAL: Supabase keys not found. Check your .env file!")
    exit()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

COM_PORT = 'COM6' 
BAUD_RATE = 115200

try:
    print(f"📡 Amrit Vaayu Hardware Bridge connecting to {COM_PORT}...")
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    print("✅ Connection Established. Listening for AWD Edge Node data...")
except Exception as e:
    print(f"❌ Failed to connect to ESP32: {e}")
    exit()

while True:
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            if line.startswith("{") and line.endswith("}"):
                data = json.loads(line)
                print(f"[{time.strftime('%H:%M:%S')}] Edge Payload: {data}")
                
                # Push to Supabase
                supabase.table("awd_logs").insert({
                    "farmer_id": 1, 
                    "image_url": "IoT_Sensor_Node",
                    "state_wet_dry": data.get("awd_state", "Unknown")
                }).execute()
                print("☁️ Synced to Supabase Cloud.")
                
    except json.JSONDecodeError:
        pass 
    except Exception as e:
        print(f"❌ Supabase Sync Error: {e}") # THIS WILL SHOW US THE FIX
        
    time.sleep(1)