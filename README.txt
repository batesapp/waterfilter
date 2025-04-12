========================================
WATER FILTER CONTROLLER
========================================

A MicroPython-based controller for a water filter system using an RP2040 microcontroller.

OVERVIEW
--------
This project implements a water filter controller that manages the operation of a water filter system. 
It provides visual feedback through an RGB LED and accepts user input through a button.
The controller supports both normal operation and a training mode to customize timing.

HARDWARE REQUIREMENTS
--------------------
- RP2040 Microcontroller (e.g., Raspberry Pi Pico, RP2040-Zero)
- Button connected to GPIO Pin 27 (with pull-down resistor)
- NeoPixel RGB LED connected to GPIO Pin 16
- Control output on GPIO Pin 5

SOFTWARE DEPENDENCIES
--------------------
- MicroPython v1.19 or later
- Required MicroPython modules:
  - machine (for GPIO and Timer control)
  - neopixel (for RGB LED control)
  - time (for timing functions)

FEATURES
--------
1. Button Operation:
   - Short press: Start normal operation sequence
   - Long press (≥ 2 seconds): Enter training mode
   - Press during sequence: Cancel current operation

2. LED Indicators:
   - Green (low): Standby/Idle state
   - Blue (low): Button pressed
   - Green (blinking): Normal operation sequence
   - Orange (3 flashes): Training mode save successful
   - Red (3 quick flashes): Training mode save failed
   - Red (1 second): Operation complete

3. Operation Modes:
   - Normal Operation: Runs the filter for a configured duration
   - Training Mode: Allows setting a custom duration

4. Configuration:
   - Timing configuration stored in settings.txt
   - Persists across reboots
   - Default timing (50 seconds) if no configuration present

INSTALLATION
------------
1. Install MicroPython on your RP2040 microcontroller
2. Copy the following files to the microcontroller:
   - main.py
   - neopixel_colors.py

DEVELOPMENT SETUP
----------------
For development and testing on a computer:

1. Create a virtual environment:
   python -m venv venv

2. Activate the virtual environment:
   - Windows: venv\Scripts\activate.bat
   - PowerShell: .\venv\Scripts\Activate.ps1
   - Linux/Mac: source venv/bin/activate

3. Install dependencies:
   pip install -r requirements.txt

4. Run tests:
   python -m pytest test_water_filter.py

PROJECT STRUCTURE
----------------
- main.py: Main application code
- neopixel_colors.py: Color definitions for the RGB LED
- test_mocks.py: Mock objects for testing
- test_timer.py: Tests for timer functionality
- test_water_filter.py: Main test suite
- docs/requirements.md: Detailed project requirements
- requirements.txt: Python dependencies for development

USAGE
-----
1. Connect the hardware as specified in the Hardware Requirements section
2. Power on the microcontroller
3. The LED will show green (low brightness) in standby mode
4. Short press the button to start normal operation
5. Long press the button to enter training mode and set a custom duration

LICENSE
-------
This project is provided as-is without any warranty. All rights reserved.

AUTHOR
------
Created by Bates
