from machine import Pin, ADC
import utime


# As the humidity increases, the voltage drops
global air_moisture_baseline
global water_moisture_baseline
global intervals


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
    
on_board_led = Pin(25, Pin.OUT)
relay_module = Pin(16, Pin.OUT)
moisture_sensor = ADC(Pin(26))


def read_moisture_value(number_of_lectures = 1):
    if number_of_lectures < 1:
        return None
    
    moisture_level = 0
    for i in range(0, number_of_lectures):
        moisture_level += moisture_sensor.read_u16()
        utime.sleep(1)
        on_board_led.toggle()
    
    on_board_led.value(1)
    return moisture_level/number_of_lectures


def calibrate():
    utime.sleep(1)
    global air_moisture_baseline
    air_moisture_baseline = read_moisture_value(number_of_lectures=3)
    on_board_led.value(0)
    utime.sleep(3)
    on_board_led.value(1)
    global water_moisture_baseline
    water_moisture_baseline = read_moisture_value(number_of_lectures=3)
    on_board_led.value(1)
    
    global intervals
    intervals = (air_moisture_baseline - water_moisture_baseline)/3
    
    print("Air moisture baseline:", air_moisture_baseline)
    print("Water moisture baseline:", water_moisture_baseline)
    print("intervals:",intervals)


def get_moisture_level():
    soil_moisture_value = read_moisture_value()
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
    print("Pump activated at", utime.ticks_ms())
    relay_module.value(1)
    utime.sleep(5)
    relay_module.value(0)
    print("Pump deactivated at", utime.ticks_ms())


# Init sensors
relay_module.value(0)
on_board_led.value(1)

# Main loop
calibrate()
while True:
    moisture_value, moisture_level = get_moisture_level()
    print("Moisture value:", moisture_value)
    print("Moisture level:", LEVEL_MAP[moisture_level])
    if moisture_level <= NORMAL_SOIL:
        activate_pump()
    utime.sleep(10)
