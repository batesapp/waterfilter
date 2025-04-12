from machine import Pin, Timer
from neopixel import NeoPixel
import time

# Hardware Configuration
LED_PIN = 16    # The LED is connected to GPIO pin 16 on RP2040-Zero
BUTTON_PIN = 27 # Input pin for trigger
CONTROL_PIN = 5 # Control output pin

# Color Components (0-255, GRB order)
COLOR_OFF = 0
COLOR_LOW = 64  # 25% brightness

# Timing Configuration (in milliseconds)
BLINK_PERIOD_MS = 500        # 0.5 seconds per blink
TOTAL_BLINK_TIME_MS = 50000  # 50 seconds total blinking time
RED_SHOW_TIME_MS = 1000      # 1 second red warning
START_LOCKOUT_MS = 1000      # 1 second lockout when starting
COMPLETE_BLUE_TIME_MS = 1000 # 1 seconds blue on completion
DEBOUNCE_MS = 100           # Button debounce time

class LEDController:
    # Colors - GRB order (Green, Red, Blue)
    OFF = (COLOR_OFF, COLOR_OFF, COLOR_OFF)
    RED_LOW = (COLOR_OFF, COLOR_LOW, COLOR_OFF)
    GREEN_LOW = (COLOR_LOW, COLOR_OFF, COLOR_OFF)
    BLUE_LOW = (COLOR_OFF, COLOR_OFF, COLOR_LOW)
    PINK_LOW = (COLOR_OFF, COLOR_LOW, COLOR_LOW)  # Mix of red and blue for pink
    
    def __init__(self, pin_num):
        self.led = NeoPixel(Pin(pin_num), 1)
        self.current_color = self.GREEN_LOW
        self.is_on = True
        
    def set_color(self, color):
        self.current_color = color
        self.led[0] = color
        self.led.write()
        self.is_on = True
        
    def turn_off(self):
        self.led[0] = self.OFF
        self.led.write()
        self.is_on = False
        
    def toggle(self):
        if self.is_on:
            self.turn_off()
        else:
            self.set_color(self.current_color)

class WaterFilter:
    # States
    IDLE = 'IDLE'
    STARTING = 'STARTING'
    BLINKING = 'BLINKING'
    STOPPING = 'STOPPING'
    COMPLETING = 'COMPLETING'
    
    def __init__(self):
        # Initialize LED
        self.led = LEDController(LED_PIN)
        
        # Initialize pin5
        self.pin5 = Pin(CONTROL_PIN, Pin.OUT)
        
        # Initialize button with interrupt
        self.button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
        self.button.irq(trigger=Pin.IRQ_RISING, handler=self._button_handler)
        
        # Initialize timers
        self.blink_timer = Timer()
        self.stop_timer = Timer()
        self.start_timer = Timer()
        self.complete_timer = Timer()
        
        # State management
        self.state = self.IDLE
        self.last_press = 0  # For debouncing
        
        # Start in idle state with green light
        self.led.set_color(self.led.GREEN_LOW)
    
    def _button_handler(self, pin):
        # Debounce
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_press) < DEBOUNCE_MS:
            return
        self.last_press = current_time
        
        if self.state == self.IDLE:
            self._start_sequence()
        elif self.state == self.BLINKING:
            self._stop_sequence(show_red=True)
        # Ignore button presses in other states
    
    def _blink_handler(self, timer):
        self.led.toggle()
    
    def _completion_sequence(self, timer=None):
        """Show pink light for 5 seconds before returning to idle and control pin5"""
        self.state = self.COMPLETING
        # Stop all timers except complete_timer
        self.blink_timer.deinit()
        self.start_timer.deinit()
        self.stop_timer.deinit()
        
        # Turn on pin5
        self.pin5.value(1)
        
        # Show pink light and set timer to return to idle
        self.led.set_color(self.led.PINK_LOW)
        self.complete_timer.init(mode=Timer.ONE_SHOT, period=COMPLETE_BLUE_TIME_MS,
                               callback=self._return_to_idle)
        
        # Set timer to turn off pin5 after 3 seconds
        Timer().init(mode=Timer.ONE_SHOT, period=3000, callback=lambda t: self.pin5.value(0))
    
    def _return_to_idle(self, timer=None):
        # Stop all timers
        self.blink_timer.deinit()
        self.start_timer.deinit()
        self.stop_timer.deinit()
        self.complete_timer.deinit()
        # Return to idle state
        self.state = self.IDLE
        self.led.set_color(self.led.GREEN_LOW)
    
    def _start_sequence(self):
        self.state = self.STARTING
        # Start blinking immediately
        self.blink_timer.init(period=BLINK_PERIOD_MS, 
                            mode=Timer.PERIODIC,
                            callback=self._blink_handler)
        # Set timer to transition to BLINKING state after lockout period
        self.start_timer.init(period=START_LOCKOUT_MS,
                            mode=Timer.ONE_SHOT,
                            callback=self._enter_blinking_state)
        # Set timer to stop blinking after total time
        self.stop_timer.init(period=TOTAL_BLINK_TIME_MS,
                           mode=Timer.ONE_SHOT,
                           callback=self._timeout_sequence)
    
    def _enter_blinking_state(self, timer):
        self.state = self.BLINKING
    
    def _timeout_sequence(self, timer=None):
        """Handle timeout (no red light, go straight to completion)"""
        if self.state in [self.BLINKING, self.STARTING]:
            self._completion_sequence()
    
    def _stop_sequence(self, show_red=True):
        """Stop blinking and either show red or go to completion"""
        self.state = self.STOPPING
        # Stop all timers except stop_timer
        self.blink_timer.deinit()
        self.start_timer.deinit()
        
        if show_red:
            # Show red and set timer for completion
            self.led.set_color(self.led.RED_LOW)
            self.stop_timer.init(period=RED_SHOW_TIME_MS,
                               mode=Timer.ONE_SHOT,
                               callback=self._completion_sequence)
        else:
            # Go straight to completion
            self._completion_sequence()

# Create and run the water filter controller
filter = WaterFilter()

# Main loop just keeps the program running
while True:
    time.sleep(1)
