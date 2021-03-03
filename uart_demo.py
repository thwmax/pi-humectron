import serial

ser = serial.Serial('/dev/serial0', 115200, timeout=5)

while True:
    print(ser.read_until().decode("utf-8"))