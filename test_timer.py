from machine import Pin, Timer
import time

# Create output pin
pin = Pin(5, Pin.OUT)
pin.value(1)  # Start HIGH

print("Starting test")
print("Initial pin value:", pin.value())

# Create a timer to switch pin LOW for 100ms
def pin_timer(t):
    print("Timer callback at:", time.ticks_ms())
    pin.value(0)  # Switch LOW
    time.sleep_ms(100)
    pin.value(1)  # Return HIGH
    print("Pin returned HIGH at:", time.ticks_ms())

# Start timer
print("Starting timer at:", time.ticks_ms())
Timer().init(mode=Timer.ONE_SHOT, period=100, callback=pin_timer)

# Keep script running
time.sleep_ms(500)
print("Test complete")
