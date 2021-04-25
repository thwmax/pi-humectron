"""
Pi Watering system

It uses the power of micropython and raspberry pi pico in order to activate
a pump depending on the moisture level of the soil

It sends activity data via UART to another device, so logging can be performed
"""
from machine import Pin, ADC, UART
import utime
import json

conversion_factor = 3.3 / (65535)

SUPER_WET_SOIL = 3
WET_SOIL = 2
NORMAL_SOIL = 1
DRY_SOIL = 0

LEVEL_MAP = {
    SUPER_WET_SOIL: "SUPER_WET_SOIL",
    WET_SOIL: "WET_SOIL",
    NORMAL_SOIL: "NORMAL_SOIL",
    DRY_SOIL: "DRY_SOIL",
}

temp_sensor = ADC(4)
activity_led = Pin(18, Pin.OUT)
on_board_led = Pin(25, Pin.OUT)
relay_module = Pin(16, Pin.OUT)
moisture_sensor = ADC(Pin(26))
button = Pin(15, Pin.IN, Pin.PULL_DOWN)
uart = UART(1, baudrate=38400, tx=Pin(4), rx=Pin(5))

# As the humidity increases, the voltage drops
air_moisture_baseline = 51600
water_moisture_baseline = 25000
intervals = 0


def send_message_UART(msg, format = "RAW"):
    """
    Writes a message in uart serial bus
    """
    if format.lower() == "json":
      data = json.dumps(msg)
      uart.write(str(data) + "#")
      print("used json")
    else:
      uart.write(msg + "#")
    print(msg)


def read_moisture_value(number_of_lectures = 1):
    if number_of_lectures < 1:
        return None
    
    moisture_level = 0
    for i in range(0, number_of_lectures):
        moisture_level += moisture_sensor.read_u16()
        utime.sleep(0.1)
    
    return moisture_level/number_of_lectures

def default_calibration():
    global air_moisture_baseline
    global water_moisture_baseline
    global intervals
    
    air_moisture_baseline = 51600
    water_moisture_baseline = 25000
    intervals = (air_moisture_baseline - water_moisture_baseline)/3
    print("Invalid interval, using default values")
    

def calibrate():
    global air_moisture_baseline
    global water_moisture_baseline
    global intervals
    
    while not button.value():
        on_board_led.toggle()
        air_moisture_baseline = read_moisture_value()
        utime.sleep(0.05)
    print("Air measure registered")
    on_board_led.value(1)
    utime.sleep(0.5)

    while not button.value():
        on_board_led.toggle()
        water_moisture_baseline = read_moisture_value()
        utime.sleep(0.05)
    print("Water measure registered")
    
    intervals = (air_moisture_baseline - water_moisture_baseline)/3
    print("range size:",intervals)
    if intervals < 1000:
        default_calibration()
    
    send_message_UART("AIR {}".format(air_moisture_baseline))
    send_message_UART("WATER {}".format(water_moisture_baseline))
    on_board_led.value(0)


def get_moisture_level():
    """
    Moisture level is measured as voltage from the sensor, 
    so as the humidity increases, the voltage drops, this method translates that 
    measure into a constant range, that can be DRY, NORMAL, WET, SUPER WET
    """
    soil_moisture_value = read_moisture_value(number_of_lectures=3)
    percentage = 100 - (soil_moisture_value * 100 / air_moisture_baseline)
    if (
        soil_moisture_value > water_moisture_baseline
        and soil_moisture_value < (water_moisture_baseline + intervals)
    ):
        return soil_moisture_value, WET_SOIL, percentage
    elif (
        soil_moisture_value > (water_moisture_baseline + intervals)
        and soil_moisture_value < (air_moisture_baseline - intervals)
    ):
        return soil_moisture_value, NORMAL_SOIL, percentage
    elif (
        soil_moisture_value < air_moisture_baseline
        and soil_moisture_value > (air_moisture_baseline - intervals)
    ):
        return soil_moisture_value, DRY_SOIL, percentage

    return soil_moisture_value, SUPER_WET_SOIL, percentage


def activate_pump():
    send_message_UART("PUMP_ON")
    relay_module.value(1)
    utime.sleep(5)
    relay_module.value(0)
    send_message_UART("PUMP_OFF")


def read_temperature():
  reading = temp_sensor.read_u16() * conversion_factor
  return 27 - (reading - 0.706)/0.001721

# Init sensors
on_board_led.value(1)
relay_module.value(0)

print("Calibrating Humectron...")
# Calibrate air and water measures
#calibrate()
default_calibration()
print("Calibration finished")

# Main loop
while True:
    moisture_value, moisture_level, percentage = get_moisture_level()
    data = {
      "moisture": percentage,
      "level": LEVEL_MAP[moisture_level],
      "temp": read_temperature(),
    }
    send_message_UART(data, format="json")
    #if moisture_level < NORMAL_SOIL:
    #    activate_pump()
    utime.sleep(30)
