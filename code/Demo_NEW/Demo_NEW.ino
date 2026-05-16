#include "Pervasive_Wide_Small.h"

#define DISPLAY_EN 6
#define LED_PIN 25
#define FRAME_SIZE 3968

uint8_t oldImage[FRAME_SIZE];
uint8_t newImage[FRAME_SIZE];

Pervasive_Wide_Small myDriver(eScreen_EPD_206_KS_0E, boardRaspberryPiPico_RP2040);

void blink(int count, int on_ms = 120, int off_ms = 120) {
  for (int i = 0; i < count; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(on_ms);
    digitalWrite(LED_PIN, LOW);
    delay(off_ms);
  }
  delay(1000);
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(DISPLAY_EN, OUTPUT);

  for (int i = 0; i < FRAME_SIZE; i++) {
    oldImage[i] = 0xFF;  // old image: white
    newImage[i] = 0x00;  // new image: black
  }

  blink(1);

  digitalWrite(DISPLAY_EN, HIGH);
  delay(3000);
  blink(2);

  hV_HAL_begin();
  blink(3);

  myDriver.begin();
  blink(4);

  myDriver.updateFast(oldImage, newImage, FRAME_SIZE);
  blink(5);
}

void loop() {
  blink(1, 500, 500);
}