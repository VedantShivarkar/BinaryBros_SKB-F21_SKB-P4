#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// --- 1. NETWORK & CLOUD CREDENTIALS ---
// 🚨 CHANGE THESE TO YOUR MOBILE HOTSPOT OR VENUE WIFI 🚨
const char* WIFI_SSID = "Nord 4";
const char* WIFI_PASSWORD = "11223344";

const char* SUPABASE_URL = "https://qsyeeroqsrubasiwopny.supabase.co/rest/v1/esp32_telemetry";
const char* SUPABASE_KEY = "sb_secret_US2EGCYXQJzishUaWWszPA_8UENi4KE";

// --- 2. PIN DEFINITIONS & SENSOR VARS ---
#define DHTPIN 4
#define DHTTYPE DHT22
#define MOISTURE_PIN 34 
#define RELAY_IN1 26 
#define RELAY_IN2 27 
#define STATUS_LED 2

DHT dht(DHTPIN, DHTTYPE);
const int AirValue = 2560;   
const int WaterValue = 1220; 

// --- 3. STATE TRACKING FOR DELTA SYNC (THE FIX) ---
String lastPumpStatus = "UNKNOWN";
unsigned long lastSyncTime = 0;
const unsigned long HEARTBEAT_INTERVAL = 3600000; // 1 Hour in milliseconds

void setup() {
  Serial.begin(115200);
  
  pinMode(STATUS_LED, OUTPUT);
  pinMode(RELAY_IN1, OUTPUT);
  pinMode(RELAY_IN2, OUTPUT);
  digitalWrite(RELAY_IN1, HIGH); // Relay OFF natively
  digitalWrite(RELAY_IN2, HIGH);
  
  dht.begin();

  // --- CONNECT TO WIFI ---
  Serial.print("📡 Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(STATUS_LED, !digitalRead(STATUS_LED)); // Blink while connecting
  }
  
  digitalWrite(STATUS_LED, HIGH); // Solid ON means Wi-Fi Connected
  Serial.println("\n✅ Wi-Fi Connected!");
  Serial.print("📍 IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // 1. Read Sensors locally (Happens every 2 seconds)
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  int moistureValue = analogRead(MOISTURE_PIN);
  
  int moisturePercent = map(moistureValue, AirValue, WaterValue, 0, 100);
  moisturePercent = constrain(moisturePercent, 0, 100); 
  
  // 2. AWD Core Logic & Relay Control
  String awdState = (moisturePercent > 60) ? "Wet" : "Dry";
  String pumpStatus = "OFF";

  if(awdState == "Dry") {
    digitalWrite(RELAY_IN1, LOW); // Turn ON pump
    pumpStatus = "ON";
  } else {
    digitalWrite(RELAY_IN1, HIGH);  // Turn OFF pump
    pumpStatus = "OFF";
  }

  // 3. ENTERPRISE FIX: EVENT-DRIVEN DELTA SYNC
  // Only upload to the cloud IF the pump state changed, OR if 1 hour has passed
  if (pumpStatus != lastPumpStatus || (millis() - lastSyncTime > HEARTBEAT_INTERVAL)) {
    
    Serial.println("⚠️ STATE CHANGE DETECTED! Preparing Cloud Sync...");

    JsonDocument doc;
    doc["moisture_val"] = moistureValue;
    doc["pump_status"] = pumpStatus;
    
    String jsonPayload;
    serializeJson(doc, jsonPayload);

    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(SUPABASE_URL);
      
      http.addHeader("Content-Type", "application/json");
      http.addHeader("apikey", SUPABASE_KEY);
      http.addHeader("Authorization", String("Bearer ") + SUPABASE_KEY);
      http.addHeader("Prefer", "return=minimal"); 

      int httpResponseCode = http.POST(jsonPayload);
      
      if (httpResponseCode > 0) {
        Serial.print("☁️ Cloud Sync Success! HTTP: ");
        Serial.println(httpResponseCode);
        
        // Update our memory so we don't send this same state again
        lastPumpStatus = pumpStatus;
        lastSyncTime = millis();
      } else {
        Serial.print("❌ Cloud Sync Failed. HTTP: ");
        Serial.println(httpResponseCode);
      }
      http.end();
    } else {
      Serial.println("⚠️ Wi-Fi Disconnected. Reconnecting...");
      WiFi.reconnect();
    }
  }

  // Very short delay so the physical water pump reacts instantly to dry dirt
  delay(2000); 
}