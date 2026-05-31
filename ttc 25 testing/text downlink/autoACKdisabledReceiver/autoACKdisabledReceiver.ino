#include <SPI.h>
#include <RF24.h>

RF24 radio(7, 8);
const byte address[6] = "00001"; 

void setup() {
  Serial.begin(9600);
  while (!Serial);
  
  Serial.println("--- Receiver Booting Up ---");
  
  if (!radio.begin()) {
    Serial.println("ERROR: Receiver NRF24 hardware is not responding.");
    while (1);
  }
  
  radio.openReadingPipe(0, address);
  
  // The Nuclear Option Settings (Must match transmitter):
  radio.setChannel(115);
  radio.setPALevel(RF24_PA_LOW);
  radio.setDataRate(RF24_250KBPS);
  radio.setAutoAck(false); 
  
  radio.startListening();
  Serial.println("Listening for incoming messages...");
}

void loop() {
  if (radio.available()) {
    char text[32] = ""; 
    radio.read(&text, sizeof(text));
    
    Serial.print("Message Received: ");
    Serial.println(text);
  }
}