#include <Adafruit_BNO055.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <utility/imumaths.h>
#include <SPI.h>
#include <LoRa.h>


#define LORA_NSS 10
#define LORA_RST 9
#define LORA_DIO0 2

float flt_x;
float flt_y;
float flt_z;

const int size=6;
uint8_t packet[size];

uint8_t ui_x;
uint8_t ui_y;
uint8_t ui_z;

int spreadingFactor = 7;
long bandwidth = 125E3; 
int txPower = 14;  

Adafruit_BNO055 bno = Adafruit_BNO055(55);

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
  Serial.println("LoRa TX ready");

  bno.begin();
  bno.setExtCrystalUse(true);

}

void loop() {
  sensors_event_t event; 
  bno.getEvent(&event);
  
  flt_x=100*event.orientation.x;
  flt_y=100*event.orientation.y;
  flt_z=100*event.orientation.z;

  ui_x=(uint16_t)(~(int)flt_x+1);
  ui_y=(uint16_t)(~(int)flt_y+1);
  ui_z=(uint16_t)(~(int)flt_z+1);

  packet[0]=ui_x>>8; packet[1]=ui_x & 0xFF;
  packet[2]=ui_y>>8; packet[3]=ui_y & 0xFF;
  packet[4]=ui_z>>8; packet[5]=ui_z & 0xFF; 
  

  sendBeacon(packet);
  delay(1000);

}

void sendBeacon(uint8_t *pac){
  // normal stuff, just sending beacon
  LoRa.beginPacket();
  LoRa.write(pac, sizeof(pac));
  LoRa.endPacket();
  Serial.println("TX done");
}
