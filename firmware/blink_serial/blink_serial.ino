// LED pins: ESP32 = 2 Arduino Nano: 13 Pi Pico: LED_BUILTIN
#define LED LED_BUILTIN

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  delay(1000);
  Serial.println("ESP32 Serial Communication Initialized.");

  pinMode(LED, OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.println("Hello World!");
  digitalWrite(LED, HIGH);
  delay(500);
  digitalWrite(LED, LOW);
  delay(500);
}
