import serial
import pyaudio
import time

# --- Serial Configuration ---
# CHANGE THIS to match your Arduino's port! 
# (e.g., 'COM3' for Windows, or '/dev/cu.usbmodem14101' for Mac)
SERIAL_PORT = '/dev/cu.usbserial-110'
BAUD_RATE = 115200 # A fast baud rate is required to push audio quickly

# --- Audio Configuration ---
CHUNK = 32               # 32 bytes perfectly matches the nRF24L01 max payload
FORMAT = pyaudio.paUInt8 # 8-bit audio (easiest for the Arduino to handle)
CHANNELS = 1             # Mono
RATE = 8000              # 8kHz sample rate (fits within the Serial bandwidth)

print(f"Connecting to Arduino on {SERIAL_PORT}...")
try:
    arduino_serial = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0)
    time.sleep(2) # Give Arduino 2 seconds to reset after opening serial port
    print("Connected!")
except Exception as e:
    print(f"Error opening serial port: {e}")
    exit()

print("Initializing Microphone...")
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("Recording and sending to Arduino... (Press Ctrl+C to stop)")

try:
    while True:
        # 1. Read exactly 32 bytes of audio from the microphone
        data = stream.read(CHUNK, exception_on_overflow=False)
        
        # 2. Blast those 32 bytes directly down the USB cable to the Arduino
        arduino_serial.write(data)
            
except KeyboardInterrupt:
    print("\nStopping stream...")
finally:
    # Clean up and close ports gracefully
    stream.stop_stream()
    stream.close()
    p.terminate()
    arduino_serial.close()
    print("Closed.")