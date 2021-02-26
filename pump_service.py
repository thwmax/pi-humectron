from machine import Pin, ADC
import utime
import _thread

MAX_VOLTAGE_LEVEL = 65535
moisture_threshold_percentage = 0.6

on_board_led = Pin(25, Pin.OUT)
relay_module = Pin(16, Pin.OUT)
moisture_sensor = ADC(Pin(26))

# As the humidity increases, the voltagedrops
global water_moisture_level

moisture_threshold = MAX_VOLTAGE_LEVEL * moisture_threshold_percentage
print("moisture threshold:", moisture_threshold)


def blink_led():
    on_board_led.value(0)
    for i in range(0, 3):
        on_board_led.toggle()
        utime.sleep(0.5)


def calibrate():    
    blink_led()
    on_board_led.value(1)
    
    global water_moisture_level
    water_moisture_level = MAX_VOLTAGE_LEVEL
    print("Water moisture level:", water_moisture_level)
    blink_led()


def get_moisture_level_thread():
    while True:
        measured_moisture = MAX_VOLTAGE_LEVEL - moisture_sensor.read_u16()
        print("Moisture:", measured_moisture)
        if measured_moisture <= moisture_threshold:
            global trigger_pump
            trigger_pump = True
        utime.sleep(20)


relay_module.value(0)
#calibrate()
on_board_led.value(1)
#_thread.start_new_thread(get_moisture_level_thread, ())


def activate_pump():
    print("Pump activated at", utime.ticks_ms())
    relay_module.value(1)
    utime.sleep(10)
    relay_module.value(0)
    print("Pump deactivated at", utime.ticks_ms())


while True:
    measured_moisture = MAX_VOLTAGE_LEVEL - moisture_sensor.read_u16()
    print("Moisture:", measured_moisture)
    if measured_moisture <= moisture_threshold:
        activate_pump()
    utime.sleep(20)


