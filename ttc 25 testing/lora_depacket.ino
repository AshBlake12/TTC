#include <SPI.h>
#include <LoRa.h>

#define LORA_NSS 10
#define LORA_RST 9
#define LORA_DIO0 2

uint8_t relayLen = 0;

float flt_x;
float flt_y;
float flt_z;
uint8_t packet[3];

uint16_t ui_x;
uint16_t ui_y;
uint16_t ui_z;

int spreadingFactor = 7;
long bandwidth = 125E3; 
int txPower = 14;  

void setup() {
  Serial.begin(9600);

  LoRa.setPins(LORA_NSS, LORA_RST, LORA_DIO0);
  if (!LoRa.begin(433E6)) {
    Serial.println("LoRa init failed");
    while(1);
  }

  LoRa.setSpreadingFactor(spreadingFactor);
  LoRa.setSignalBandwidth(bandwidth);
  LoRa.setCodingRate4(8);
  LoRa.setSyncWord(0x22);
  LoRa.setTxPower(txPower);
  LoRa.enableCrc(); 
  Serial.println("LoRa RX ready");


}

void loop() {
  
  readRelay();

  ui_x=((uint16_t)packet[0]<<8) | packet[1];
  ui_y=((uint16_t)packet[2]<<8) | packet[3];
  ui_z=((uint16_t)packet[4]<<8) | packet[5];

  flt_x = (float)(~(int16_t)ui_x+1)/100.0;
  flt_y = (float)(~(int16_t)ui_y+1)/100.0;
  flt_z = (float)(~(int16_t)ui_z+1)/100.0;


  Serial.print(flt_x);
  Serial.print(flt_y);
  Serial.print(flt_z);

}

void readRelay(){
  //probably we should add some signature (our call sign?) so we dont read random loras ka data uring uplink, or we can also add command parsing for kill code and end uplink stuff 
  int packetSize = LoRa.parsePacket();
  if (!packetSize) return;
  relayLen = 0;
  while (LoRa.available() && relayLen < 32) {
    packet[relayLen++] = LoRa.read();
  }
}
