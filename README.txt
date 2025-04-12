Water Filter Controller
=====================

A Python-based controller for managing water filter operations using a Raspberry Pi Pico (RP2040).

Features
--------
- LED status indication (green, red, blue, orange)
- Button control for operation and configuration
- Configurable timing settings
- Persistent configuration storage
- Power-saving idle mode

Hardware Requirements
-------------------
- Raspberry Pi Pico (RP2040)
- NeoPixel LED
- Push button
- Water filter control relay

Pin Configuration
----------------
- LED_PIN: 16 (GPIO pin for NeoPixel LED)
- BUTTON_PIN: 27 (Input pin for trigger)
- CONTROL_PIN: 5 (Control output pin for water filter)

Setup Instructions
-----------------
1. Clone the repository:
   git clone [repository-url]

2. Set up Python environment:
   ./setup_python.sh

3. Upload the code to your Raspberry Pi Pico:
   - Connect the Pico to your computer
   - Copy main.py to the Pico's filesystem

4. Connect the hardware:
   - Connect LED to GPIO 16
   - Connect button to GPIO 27
   - Connect control relay to GPIO 5

Usage
-----
- Short press: Start water filter operation
- Long press (2 seconds): Enter configuration mode
- During operation: Press button to cancel

Configuration
------------
- Press and hold button for 2 seconds to enter training mode
- Release button when desired timing is reached
- LED will flash orange 3 times to confirm successful save

Default Settings
---------------
- Blink period: 500ms
- Long press duration: 2000ms
- Pin5 on time: 250ms
- Red warning time: 1000ms
- Idle timeout: 5000ms

Troubleshooting
--------------
- If LED doesn't light up: Check connections and power supply
- If button doesn't respond: Check button connection and pull-down resistor
- If configuration doesn't save: Check file system permissions

License
-------
[Add your license information here]

Maintenance
----------
- Keep the code updated with the latest MicroPython version
- Regularly check hardware connections
- Monitor LED brightness and adjust if needed 



NOTE: Use Thonny IDE for uploading code to the Pico.
