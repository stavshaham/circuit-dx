/*
 * cap_meter.ino — measure capacitance with an Arduino Nano (circuit-dx)
 *
 * Method: charge the capacitor through a known resistance R and time how long
 * the voltage takes to reach a fixed fraction of the supply. For an RC circuit,
 *     V(t) = Vcc * (1 - e^(-t / RC))   →   C = t / (R * -ln(1 - V/Vcc))
 * The threshold is a fixed ADC count, so the result does not depend on the
 * exact USB supply voltage (the ADC is ratiometric to Vcc).
 *
 * Wiring (keep this separate from Circuit 1 and the ESP32):
 *   D8 ──[R10k-b]──[R10k-c]──[R10k-d]──┬── A0
 *                                       C  (capacitor under test)
 *   GND ────────────────────────────────┘
 *   Electrolytic capacitors: + (long leg) to the A0 side, stripe to GND.
 *
 * Usage: open the Serial Monitor at 115200 baud, insert a capacitor,
 * press Enter to measure. Swap the capacitor and press Enter again.
 */

#include <math.h>

const uint8_t CHARGE_PIN = 8;
const uint8_t SENSE_PIN  = A0;

// Sum of the MEASURED values of the series resistors (from parts.csv):
// R10k-b + R10k-c + R10k-d (measured 2026-10-17)
const float R_OHMS = 29480.0;   // 9800 + 9700 + 9980

const int  THRESHOLD     = 647;   // ADC counts, ≈ 63.2% of full scale (one time constant)
const int  DISCHARGED    = 2;     // ADC counts considered "empty"
const int  RUNS          = 20;    // measurements averaged per capacitor
const unsigned long CHARGE_TIMEOUT_US   = 3000000UL;  // 3 s
const unsigned long DISCHARGE_TIMEOUT_MS = 10000UL;   // 10 s

// -ln(1 - THRESHOLD/1024): number of time constants to reach the threshold
const float K = -log(1.0 - THRESHOLD / 1024.0);

bool discharge() {
  digitalWrite(CHARGE_PIN, LOW);                 // discharge back through R
  unsigned long start = millis();
  while (analogRead(SENSE_PIN) > DISCHARGED) {
    if (millis() - start > DISCHARGE_TIMEOUT_MS) return false;
  }
  delay(20);                                     // let it settle fully
  return true;
}

// Returns charge time in microseconds, or 0 on timeout
unsigned long chargeTimeUs() {
  unsigned long t0 = micros();
  digitalWrite(CHARGE_PIN, HIGH);
  while (analogRead(SENSE_PIN) < THRESHOLD) {
    if (micros() - t0 > CHARGE_TIMEOUT_US) {
      digitalWrite(CHARGE_PIN, LOW);
      return 0;
    }
  }
  unsigned long dt = micros() - t0;
  digitalWrite(CHARGE_PIN, LOW);
  return dt;
}

void measure() {
  float sum = 0, sumSq = 0;
  int ok = 0;

  for (int i = 0; i < RUNS; i++) {
    if (!discharge()) {
      Serial.println("  Could not discharge — check the wiring.");
      return;
    }
    unsigned long dt = chargeTimeUs();
    if (dt == 0) {
      Serial.println("  Timeout — capacitor too large, or nothing connected to D8.");
      return;
    }
    float c_nF = (dt * 1e-6) / (R_OHMS * K) * 1e9;
    sum += c_nF;
    sumSq += c_nF * c_nF;
    ok++;
  }

  float mean = sum / ok;
  float sd = sqrt(max(0.0, sumSq / ok - mean * mean));

  if (mean < 1.0) {
    Serial.println("  No capacitor detected (< 1 nF).");
    return;
  }
  Serial.print("  C = ");
  Serial.print(mean, 1);
  Serial.print(" nF   (spread ±");
  Serial.print(sd, 1);
  Serial.print(" nF over ");
  Serial.print(ok);
  Serial.println(" runs)");
}

void setup() {
  Serial.begin(115200);
  pinMode(CHARGE_PIN, OUTPUT);
  digitalWrite(CHARGE_PIN, LOW);

  // Faster ADC: prescaler 16 → ~13 µs per reading instead of ~112 µs,
  // so the threshold crossing is timed more precisely.
  ADCSRA = (ADCSRA & ~0x07) | 0x04;

  Serial.println("circuit-dx capacitance meter (Nano)");
  Serial.print("Series resistance: ");
  Serial.print(R_OHMS, 0);
  Serial.println(" ohm");
  Serial.println("Insert a capacitor and press Enter to measure.");
}

void loop() {
  if (Serial.available()) {
    while (Serial.available()) Serial.read();    // clear the input line
    Serial.println("Measuring...");
    measure();
    Serial.println("Ready — swap the capacitor and press Enter.");
  }
}
