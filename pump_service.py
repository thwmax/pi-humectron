"""
Pi Watering system

It uses the power of micropython and raspberry pi pico in order to activate
a pump depending on the moisture level of the soil

It sends activity data via UART to another device, so logging can be performed
"""
from machine import Pin, ADC, UART
import utime

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


activity_led = Pin(18, Pin.OUT)
on_board_led = Pin(25, Pin.OUT)
relay_module = Pin(16, Pin.OUT)
moisture_sensor = ADC(Pin(26))
button = Pin(15, Pin.IN, Pin.PULL_DOWN)
uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))

# As the humidity increases, the voltage drops
air_moisture_baseline = 51600
water_moisture_baseline = 25000
intervals = 0


def send_message_UART(msg):
    """
    Writes a message in uart serial bus
    """
    uart.write(msg + "-")
    print(msg)


def read_moisture_value(number_of_lectures = 1):
    if number_of_lectures < 1:
        return None
    
    moisture_level = 0
    for i in range(0, number_of_lectures):
        moisture_level += moisture_sensor.read_u16()
        utime.sleep(0.1)
    
    return moisture_level/number_of_lectures


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
        air_moisture_baseline = 51600
        water_moisture_baseline = 25000
        intervals = (air_moisture_baseline - water_moisture_baseline)/3
        print("Invalid interval, using default values")
    
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
    if (
        soil_moisture_value > water_moisture_baseline
        and soil_moisture_value < (water_moisture_baseline + intervals)
    ):
        return soil_moisture_value, WET_SOIL
    elif (
        soil_moisture_value > (water_moisture_baseline + intervals)
        and soil_moisture_value < (air_moisture_baseline - intervals)
    ):
        return soil_moisture_value, NORMAL_SOIL
    elif (
        soil_moisture_value < air_moisture_baseline
        and soil_moisture_value > (air_moisture_baseline - intervals)
    ):
        return soil_moisture_value, DRY_SOIL

    return soil_moisture_value, SUPER_WET_SOIL


def activate_pump():
    send_message_UART("PUMP_ON")
    relay_module.value(1)
    utime.sleep(5)
    relay_module.value(0)
    send_message_UART("PUMP_OFF")


# Init sensors
activity_led.value(1)
relay_module.value(0)

print("Calibrating Humetron...")
# Calibrate air and water measures
calibrate()
print("Calibration finished")

# Main loop
while True:
    moisture_value, moisture_level = get_moisture_level()
    send_message_UART("M {} {}".format(moisture_value, LEVEL_MAP[moisture_level]))
    if moisture_level < NORMAL_SOIL:
        activate_pump()
    utime.sleep(30)
