
#include <RF24.h>

// Set up nRF24L01 on pins 7 (CE) and 8 (CSN)
RF24 radio(7, 8); 

// A completely arbitrary 5-letter address for our radio pipe
const byte address[6] = "AUDIO"; 

// A buffer to hold exactly 32 bytes of audio
byte payload[32]; 

void setup() {
  // Must match the baud rate in our Python script!
  Serial.begin(115200); 
  
  radio.begin();
  radio.openWritingPipe(address);
  
  // Set to max power and fastest speed for audio streaming
  radio.setChannel(115);
  radio.setPALevel(RF24_PA_MAX);
  radio.setDataRate(RF24_2MBPS);
  radio.setAutoAck(false); 
  
  // We are only transmitting, so stop listening
  radio.stopListening(); 
}

void loop() {
  // If the Mac has pushed at least 32 bytes down the USB...
  if (Serial.available() >= 32) {
    // ...scoop them up into our payload array...
    Serial.readBytes(payload, 32);
    // ...and blast them into the air!
    radio.write(&payload, sizeof(payload));
  }
}