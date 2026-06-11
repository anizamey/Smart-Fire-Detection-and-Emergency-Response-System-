#include <Servo.h>

#define RED_LED 2
#define GREEN_LED 3
#define PIEZO 7
#define SERVO_PIN 9
#define GAS_ANALOG A0

Servo gateServo;

const int gasMin = 100;
const int gasMax = 650;
const int threshold = 50;

bool danger = false;
float gasPercent = 0;

void setup() {
  Serial.begin(9600);
  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(PIEZO, OUTPUT);
  gateServo.attach(SERVO_PIN);
  gateServo.write(45);
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(RED_LED, LOW);
}

void loop() {
  int sensorValue = analogRead(GAS_ANALOG);
  gasPercent = map(sensorValue, gasMin, gasMax, 0, 100);
  gasPercent = constrain(gasPercent, 0, 100);

  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == '1') {
      danger = (gasPercent >= threshold);
    } else if (cmd == '0') {
      danger = false;
    }
  }

  if (danger) {
    digitalWrite(RED_LED, HIGH);
    digitalWrite(GREEN_LED, LOW);
    tone(PIEZO, 1000);
    gateServo.write(135);
    Serial.print("STATE: DANGER, GAS LEVEL: ");
    Serial.println(gasPercent);
    Serial.println("FIRE_DETECTED");
  } else {
    digitalWrite(RED_LED, LOW);
    digitalWrite(GREEN_LED, HIGH);
    noTone(PIEZO);
    gateServo.write(45);
    Serial.print("STATE: SAFE, GAS LEVEL: ");
    Serial.println(gasPercent);
    Serial.println("NO_FIRE");
  }

  delay(200);
}
