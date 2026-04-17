import serial
import pyaudio

# --- Serial Configuration ---
SERIAL_PORT = 'COM3' # <--- CHANGE THIS TO YOUR WINDOWS COM PORT
BAUD_RATE = 115200

# --- Audio Configuration ---
CHUNK = 32               # Must match the 32-byte radio payload
FORMAT = pyaudio.paUInt8 # 8-bit audio
CHANNELS = 1             # Mono
RATE = 8000              # 8kHz sample rate

print(f"Connecting to Arduino Receiver on {SERIAL_PORT}...")
try:
    # timeout=None means it will wait forever for data
    arduino_serial = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=None) 
    print("Connected!")
except Exception as e:
    print(f"Error opening serial port: {e}")
    exit()

print("Initializing Speakers...")
p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True) # Output=True means it plays to speakers

print("Listening for audio... (Press Ctrl+C to stop)")

try:
    while True:
        # Check if exactly 32 bytes have arrived from the Arduino
        if arduino_serial.in_waiting >= CHUNK:
            # Read the bytes from the USB port
            data = arduino_serial.read(CHUNK)
            # Instantly push them to the computer speakers
            stream.write(data)
            
except KeyboardInterrupt:
    print("\nStopping stream...")
finally:
    # Clean up
    stream.stop_stream()
    stream.close()
    p.terminate()
    arduino_serial.close()
    print("Closed.")