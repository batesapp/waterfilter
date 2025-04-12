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
CONFIG_BLINK_PERIOD_MS = 200  # 0.2 seconds per blink in config mode (rapid)
BUTTON_LONG_PRESS_MS = 2000  # 2 seconds for long press
PIN5_ON_TIME_MS = 250      # 250ms for pin5 on time
RED_SHOW_TIME_MS = 1000     # 1 second red warning
FLASH_ERROR_TIME_MS = 250   # Time for error flash
COMPLETE_BLUE_TIME_MS = 1000 # 1 seconds blue on completion
DEBOUNCE_MS = 100           # Button debounce time
IDLE_TIMEOUT_MS = 5000     # 5 seconds timeout for LED in IDLE state
SETTINGS_FILE = "settings.txt"  # File to store configuration
START_LOCKOUT_MS = 1000      # 1 second lockout when starting

# Default configuration
DEFAULT_BLINK_TIME = 50000  # Default value if no saved state (50 seconds)

def save_to_file(duration_ms):
    """Save duration to file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            f.write(str(duration_ms))
        return True
    except:
        return False

def read_from_file():
    """Read duration from file, return default if file doesn't exist"""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return int(f.read().strip())
    except:
        return DEFAULT_BLINK_TIME

# Try to load TOTAL_BLINK_TIME_MS from file
TOTAL_BLINK_TIME_MS = read_from_file()
print(f"Loaded configuration: {TOTAL_BLINK_TIME_MS}ms ({TOTAL_BLINK_TIME_MS/1000:.1f} seconds)")  # Debug

class LEDController:
    # Colors - GRB order (Green, Red, Blue)
    OFF = (COLOR_OFF, COLOR_OFF, COLOR_OFF)
    RED_LOW = (COLOR_OFF, COLOR_LOW, COLOR_OFF)
    GREEN_LOW = (COLOR_LOW, COLOR_OFF, COLOR_OFF)
    BLUE_LOW = (COLOR_OFF, COLOR_OFF, COLOR_LOW)
    ORANGE_LOW = (10, 128, COLOR_OFF)  # Mix of green and red for orange
    
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
    BLINKING = 'BLINKING'
    TRAINING = 'TRAINING'
    SLEEPING = 'SLEEPING'
    
    def __init__(self):
        # Initialize LED
        self.led = LEDController(LED_PIN)
        
        # Initialize pin5 (normally HIGH)
        self.pin5 = Pin(CONTROL_PIN, Pin.OUT)
        self.pin5.value(1)  # Set to HIGH initially
        
        # Initialize button (no interrupt)
        self.button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
        print("Initializing button on pin", BUTTON_PIN)  # Debug
        
        # Initialize timers
        self.blink_timer = Timer()
        self.start_timer = Timer()
        self.long_press_timer = Timer()
        self.button_poll_timer = Timer()  # New timer for polling button
        self.idle_timer = Timer()  # New timer for idle timeout
        
        # State management
        self.state = self.IDLE
        self.last_button_state = False  # Track previous button state
        self.button_press_start = 0  # For long press detection
        self.canceling = False  # Flag to prevent new sequence during cancellation
        
        # Start in idle state with green light
        self.led.set_color(self.led.GREEN_LOW)
        print("Initialization complete, in IDLE state")  # Debug
        
        # Start button polling
        self._start_button_polling()
        
        # Start idle timer
        self._start_idle_timer()
    
    def _start_button_polling(self):
        """Start polling the button every 100ms"""
        def poll_button(timer):
            current_state = self.button.value() == 1
            if current_state != self.last_button_state:
                current_time = time.ticks_ms()
                if current_state:  # Button pressed
                    print("Button pressed detected")  # Debug
                    self._handle_button_press(current_time)
                else:  # Button released
                    print("Button release detected")  # Debug
                    self._handle_button_release(current_time)
                self.last_button_state = current_state
        
        print("Starting button polling")  # Debug
        self.button_poll_timer.init(period=100, mode=Timer.PERIODIC, callback=poll_button)
    
    def _handle_button_press(self, current_time):
        """Handle button press - change states and provide immediate feedback"""
        print(f"Handling button press, state: {self.state}")  # Debug
        self.button_press_start = current_time
        
        if self.state == self.IDLE and not self.canceling:  # Only handle if not canceling
            # Show blue LED immediately
            self.led.set_color(self.led.BLUE_LOW)
            
            # Start timer to check for long press
            def check_long_press(timer):
                if self.button.value():  # Still pressed
                    press_duration = time.ticks_diff(time.ticks_ms(), self.button_press_start)
                    print(f"Long press check: {press_duration}ms")  # Debug
                    if press_duration >= BUTTON_LONG_PRESS_MS:
                        print("Long press detected, entering training mode")  # Debug
                        self.long_press_timer.deinit()
                        self.state = self.TRAINING
                        self._start_training_blink()
            
            self.long_press_timer.init(period=100, callback=check_long_press)
            
        elif self.state == self.SLEEPING and not self.canceling:
            print("Button pressed while in sleeping mode")  # Debug
            # Nothing to do on press, wait for release
            
        elif self.state == self.TRAINING:
            print("Button pressed while in training mode")  # Debug
            # Nothing to do on press, wait for release
            pass
            
        elif self.state == self.BLINKING:
            print("Button pressed while blinking, canceling sequence and timers")  # Debug
            self.canceling = True  # Set canceling flag
            # Cancel both blink and completion timers
            self.blink_timer.deinit()
            self.start_timer.deinit()  # Cancel the completion timer
            self._execute_stop_to_idle_action()  # This will handle the rest of cleanup and return to IDLE
    
    def _handle_button_release(self, current_time):
        """Handle button release - start sequence if it was a short press"""
        print(f"Handling button release, state: {self.state}")  # Debug
        press_duration = time.ticks_diff(current_time, self.button_press_start)
        print(f"Press duration: {press_duration}ms")  # Debug
        self.long_press_timer.deinit()
        
        if self.state == self.IDLE and press_duration < BUTTON_LONG_PRESS_MS and not self.canceling:
            print("Short press detected, starting sequence")  # Debug
            self._start_sequence()

        elif self.state == self.SLEEPING and press_duration < BUTTON_LONG_PRESS_MS and not self.canceling:
            print("Short press detected, returning to IDLE")  # Debug
            self._execute_stop_to_idle_action()
        
        elif self.state == self.TRAINING:
            print(f"Training mode release, duration: {press_duration}ms")  # Debug
            # Calculate total training time from the original press
            config_time = time.ticks_diff(current_time, self.button_press_start)
            print(f"Saving config time: {config_time}ms")  # Debug
            
            # Try to save configuration
            if save_to_file(config_time):
                print("Save successful")  # Debug
                global TOTAL_BLINK_TIME_MS
                TOTAL_BLINK_TIME_MS = config_time
                
                # Flash orange 3 times to indicate successful save
                for _ in range(3):
                    self.led.set_color(self.led.ORANGE_LOW)
                    time.sleep_ms(500)
                    self.led.turn_off()
                    time.sleep_ms(500)
            else:
                print("Save failed")  # Debug
                # If save fails, flash red 3 times rapidly
                for _ in range(3):
                    self.led.set_color(self.led.RED_LOW)
                    time.sleep_ms(FLASH_ERROR_TIME_MS)
                    self.led.turn_off()
                    time.sleep_ms(FLASH_ERROR_TIME_MS)
            
            # Execute action after save feedback
            self._execute_stop_to_idle_action()
        
        # Reset canceling flag after release
        if self.canceling:
            print("Resetting canceling flag")  # Debug
            self.canceling = False
    
    def _execute_stop_to_idle_action(self):
        """Execute the completion action: switch pin5 LOW and show red LED"""
        print(f"Executing completion action, canceling current state: {self.state}")  # Debug
        
        # Cancel any current operation by stopping all timers
        print("Stopping all timers")  # Debug
        self.blink_timer.deinit()
        self.start_timer.deinit()
        self.long_press_timer.deinit()
        
        # Switch pin5 LOW for exactly 250ms then back to HIGH
        print("Switching pin5 LOW for 250ms")  # Debug
        self.pin5.value(0)  # Switch to LOW
        time.sleep_ms(PIN5_ON_TIME_MS)  # Wait exactly 250ms
        self.pin5.value(1)  # Return to HIGH
        print("Pin5 returned to HIGH")  # Debug
        
        # Show red LED for 1 second then return to standby
        print("Showing red LED for 1 second")  # Debug
        self.led.set_color(self.led.RED_LOW)
        time.sleep_ms(RED_SHOW_TIME_MS)
        
        # Return to standby (green LED)
        print("Returning to standby (green LED)")  # Debug
        self.state = self.IDLE  # Always return to IDLE state
        self.led.set_color(self.led.GREEN_LOW)
        
        # Restart the idle timer
        self._start_idle_timer()
    
    def _start_sequence(self):
        """Start the normal blinking sequence"""
        print(f"Starting normal sequence, will run for {TOTAL_BLINK_TIME_MS}ms ({TOTAL_BLINK_TIME_MS/1000:.1f} seconds)")  # Debug
        
        # Cancel any existing timers first
        print("Canceling any existing timers")  # Debug
        self.blink_timer.deinit()
        self.start_timer.deinit()
        self.long_press_timer.deinit()
        self.idle_timer.deinit()  # Cancel idle timer when starting sequence
        
        self.state = self.BLINKING
        
        # Start blinking green
        def blink(timer):
            self.led.toggle()
            if not self.led.is_on:
                self.led.current_color = self.led.GREEN_LOW
        
        print("Starting green blink")  # Debug
        self.blink_timer.init(period=BLINK_PERIOD_MS, 
                            mode=Timer.PERIODIC,
                            callback=blink)
        
        # Set timer for completion
        print("Setting completion timer")  # Debug
        self.start_timer.init(period=TOTAL_BLINK_TIME_MS,
                            mode=Timer.ONE_SHOT,
                            callback=lambda t: self._execute_stop_to_idle_action())
    
    def _start_training_blink(self):
        """Start rapid blinking for training mode"""
        print("Starting training blink")  # Debug
        def rapid_blink(timer):
            if self.state == self.TRAINING:  # Only blink if still in training
                self.led.toggle()
                if not self.led.is_on:
                    self.led.current_color = self.led.BLUE_LOW
        
        # Stop any existing blink timer
        self.blink_timer.deinit()
        self.idle_timer.deinit()  # Cancel idle timer when entering training mode
        
        # Set initial color and start rapid blinking
        self.led.set_color(self.led.BLUE_LOW)
        self.blink_timer.init(period=CONFIG_BLINK_PERIOD_MS, callback=rapid_blink)
    
    def _start_idle_timer(self):
        """Start timer to turn off LED after idle timeout"""
        print("Starting idle timer")  # Debug
        
        # Cancel any existing idle timer first
        self.idle_timer.deinit()
        
        def idle_timeout(timer):
            # Only turn off LED if in IDLE state
            if self.state == self.IDLE:
                print("Idle timeout reached, turning off LED")  # Debug
                self.led.turn_off()
                self.state = self.SLEEPING
            else:
                print(f"Idle timeout ignored, current state: {self.state}")  # Debug
        
        # Set timer for idle timeout
        self.idle_timer.init(period=IDLE_TIMEOUT_MS,
                           mode=Timer.ONE_SHOT,
                           callback=idle_timeout)

# Create and run the water filter controller
filter = WaterFilter()

# Main loop just keeps the program running
while True:
    time.sleep(1)
