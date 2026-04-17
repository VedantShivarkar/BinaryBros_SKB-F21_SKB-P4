# Amrit Vaayu dMRV

**Team Name:** Binary Bros  
**Members:** Vedant Shivarkar (Team Lead), Akshad Kolawar  
**Hackathon Problem Statement:** SKB-P4 (Digital Monitoring, Reporting, and Verification for Carbon Markets)

## Overarching Architecture
Amrit Vaayu is a highly scalable, "Cloud-Proof" hardware-software ecosystem designed to automate and verify the Alternate Wetting and Drying (AWD) cycle for rice farming. Our goal is to drastically reduce methane (CH4) emissions while securely mapping farmers' compliance to rigorous, certifiable carbon credit ledgers.

The application spans three strict layers:
1. **IoT Edge (ESP32):** Real-time telemetric aggregation (soil moisture, DHT22) running relay-based irrigation loops and surfacing strict JSON. 
2. **AI & Communications Backend:** Synthesized Sentinel-1 SAR models mapped via PyTorch, mixed with Twilio-Groq conversational interfaces allowing farmers to verify and query their carbon credits entirely offline through standard WhatsApp NLP models.
3. **Assurance Front-End:** A high-fidelity React dashboard built beautifully visualizing aggregated SAR backscatter anomalies and a live Leaflet geolocation heatmap.

---

## Running the Application Locally

### 1. The FastAPI Backend
The backend runs on Python 3.11 combining FastAPI routing and connecting to a Supabase PostgreSQL instance.

```bash
# Open directory
cd backend

# Setup environment 
python -m venv .venv

# Activate environment
.\.venv\Scripts\activate      # Windows
source .venv/bin/activate    # Mac/Linux

# Install module constraints
pip install -r requirements.txt
```

Load your core environment variables. Create a `.env` in the backend root:
```
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
GROQ_API_KEY=your_key
```

Execute the core server logic:
```bash
uvicorn app:app --reload
```
*The API will orbit `http://127.0.0.1:8000`.*

### 2. Testing the WhatsApp Webhook (For Twilio Console)
To route physical Twilio requests to the local webhook endpoint, initialize an Ngrok tunnel:
```bash
ngrok http 8000
```
Then copy your `ngrok` forwarding URL into the Twilio Sandbox for WhatsApp webhook configuration, specifically pointing to `https://<ngrok_url>/api/whatsapp`.

### 3. The React/Vite Frontend
To initiate the gorgeous Deep-Charcoal Assurance Dashboard:
```bash
cd frontend
npm install
npm run dev
```
*The Dashboard automatically mounts to `http://localhost:5173`.*

### 4. Edge Hardware Firmware 
The edge script controls our customized analog arrays and relay circuits.
- Open the `/hardware` folder using the **PlatformIO** extension within VSCode.
- The strict dependencies (`Adafruit Unified Sensor`, `Adafruit DHT`, `ArduinoJSON`) will auto-provision via `platformio.ini`.
- Compile and Upload to the ESP32 WROOM board.
- You can hook the C++ output seamlessly logic into a python socket via the serial monitor running safely at `115200` baud.
