import serial
import json
import time
from supabase import create_client

SUPABASE_URL = "https://qsyeeroqsrubasiwopny.supabase.co"
SUPABASE_KEY = "sb_secret_US2EGCYXQJzishUaWWszPA_8UENi4KE"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

COM_PORT = 'COM6' 
BAUD_RATE = 115200

try:
    print(f"📡 Amrit Vaayu Hardware Bridge connecting to {COM_PORT}...")
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
except Exception as e:
    print(f"❌ Failed to connect to ESP32: {e}")
    exit()

while True:
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            if line.startswith("{") and line.endswith("}"):
                data = json.loads(line)
                
                # Push to Supabase
                supabase.table("esp32_telemetry").insert({
                    "moisture_val": data.get("moisture_raw", 0),
                    "pump_status": "ON" if data.get("relay_motor_active") else "OFF"
                }).execute()
                print(f"[{time.strftime('%H:%M:%S')}] ☁️ Synced to Cloud: Moisture {data.get('moisture_raw')} | Pump: {'ON' if data.get('relay_motor_active') else 'OFF'}")
                
    except Exception as e:
        pass # Ignore serial garbage
    time.sleep(2)