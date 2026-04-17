#include <Arduino.h>
#include <DHT.h>
#include <ArduinoJson.h>

// --- Pin Definitions (Binary Bros Hardware Spec) ---
// 1. DHT22 Temperature & Humidity Sensor
#define DHTPIN 4
#define DHTTYPE DHT22

// 2. Capacitive Soil Moisture Sensor (Analog reading)
#define MOISTURE_PIN 34 // ADC1 mapping

// 3. Dual Channel Relay
#define RELAY_IN1 26 // Motor/Water Pump control
#define RELAY_IN2 27 // Reserved / second valve

// 4. Onboard Status LED (Pro Move)
#define STATUS_LED 2

// Initialize DHT Sensor Class
DHT dht(DHTPIN, DHTTYPE);

// Calibration parameters for capacitive moisture scaling
// Adjust based on real dirt reading resistance!
const int AirValue = 2560;   // Sensor in open air
const int WaterValue = 1220; // Sensor completely submerged

void setup() {
  Serial.begin(115200);
  
  // Initialize IO mapping
  pinMode(STATUS_LED, OUTPUT);
  pinMode(RELAY_IN1, OUTPUT);
  pinMode(RELAY_IN2, OUTPUT);
  
  // Ensure relays are OFF natively (Assume active LOW triggers)
  digitalWrite(RELAY_IN1, HIGH);
  digitalWrite(RELAY_IN2, HIGH);
  
  dht.begin();
  
  // Flashing boot sequence for the onboard indicator
  for(int i=0; i<3; i++) {
    digitalWrite(STATUS_LED, HIGH);
    delay(150);
    digitalWrite(STATUS_LED, LOW);
    delay(150);
  }
}

void loop() {
  // Pull metrics from the DHT22
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  // Read analog frequency scaling of the moisture
  int moistureValue = analogRead(MOISTURE_PIN);
  
  // Linearly map the reading to a 0% - 100% saturation scale
  int moisturePercent = map(moistureValue, AirValue, WaterValue, 0, 100);
  moisturePercent = constrain(moisturePercent, 0, 100); // Guardrails
  
  // AWD Core Logic Determination
  // Threshold defines the point where methane flux reverses.  
  String awdState = (moisturePercent > 60) ? "Wet" : "Dry";
  
  // Relay Toggle Logic
  if(awdState == "Dry") {
    // Initiate flooding for AWD cycle compliance
    digitalWrite(RELAY_IN1, LOW); // Turn ON pump
    digitalWrite(STATUS_LED, HIGH); // Indicator ON solid showing active pumping
  } else {
    // Field is adequately saturated
    digitalWrite(RELAY_IN1, HIGH);  // Turn OFF pump
    digitalWrite(STATUS_LED, LOW);   // Indicator OFF
  }

  // Construct rigorous JSON payload for backend processing using ArduinoJson
  JsonDocument doc;
  
  // Filter NaNs to ensure parsing stability
  if (isnan(h) || isnan(t)) {
    doc["error"] = "DHT Read Failure";
  } else {
    doc["temperature_c"] = round(t * 10.0) / 10.0;
    doc["humidity_percent"] = round(h * 10.0) / 10.0;
  }
  
  doc["moisture_raw"] = moistureValue;
  doc["moisture_percent"] = moisturePercent;
  doc["awd_state"] = awdState;
  doc["relay_motor_active"] = (awdState == "Dry" ? true : false);

  // Serialize exactly as one uniform line ending in '\n'
  serializeJson(doc, Serial);
  Serial.println(); 

  // Aggregation delay (10s) ensuring edge node stability and serial coherence
  delay(10000);
}
