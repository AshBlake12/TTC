#include <SPI.h>
#include <RF24.h>

RF24 radio(7, 8);
const byte address[6] = "00001";

void setup() {
  Serial.begin(9600);
  while (!Serial);
  
  Serial.println("\n--- Transmitter Booting Up ---");
  
  if (!radio.begin()) {
    Serial.println("ERROR: NRF24 hardware is not responding.");
    while (1);
  }
  
  radio.openWritingPipe(address);
  
  // The Nuclear Option Settings:
  radio.setChannel(115);                 // Dodge WiFi
  radio.setPALevel(RF24_PA_LOW);         // Bump power up slightly
  radio.setDataRate(RF24_250KBPS);       // Slowest speed = highest reliability
  radio.setAutoAck(false);               // TURN OFF receipts (bypasses clone bugs)
  
  radio.stopListening();
  Serial.println("Setup Complete. Entering Main Loop...");
}

void loop() {
  const char text[] = "Hello World";
  
  Serial.print("Attempting to send... ");
  
  // Because Auto-ACK is off, this will ALWAYS return true now.
  // It is just shouting into the void.
  radio.write(&text, sizeof(text));
  
  Serial.println("Broadcast Sent! (No receipt requested)");
  delay(1000);
}