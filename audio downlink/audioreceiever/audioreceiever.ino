#include <nRF24L01.h>
#include <RF24.h>

// Set up nRF24L01 on pins 7 (CE) and 8 (CSN)
RF24 radio(7, 8); 

// Must match the exact 5-letter address from the transmitter
const byte address[6] = "AUDIO"; 

// A buffer to catch the 32 bytes of audio
byte payload[32]; 

void setup() {
  // Must match the Python baud rate!
  Serial.begin(115200); 
  
  radio.begin();
  radio.openReadingPipe(0, address);

  radio.setChannel(115);
  
  radio.setPALevel(RF24_PA_MAX);
  radio.setDataRate(RF24_2MBPS); 

  radio.setAutoAck(false);
  
  // We are the receiver, so start listening to the airwaves
  radio.startListening(); 
}

void loop() {
  // If the radio caught a packet from the air...
  if (radio.available()) {
    // ...read the 32 bytes into our payload array...
    radio.read(&payload, sizeof(payload));
    
    // ...and immediately shove them up the USB cable to Windows!
    Serial.write(payload, sizeof(payload));
  }
}