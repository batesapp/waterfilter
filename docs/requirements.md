# Water Filter Controller Requirements

## Hardware Requirements
- RP2040 Microcontroller
- Button connected to GPIO Pin 27 (with pull-down resistor)
- NeoPixel RGB LED connected to GPIO Pin 28
- Control output on GPIO Pin 5

## Software Dependencies
- MicroPython v1.19 or later
- Required MicroPython modules:
  - `machine` (for GPIO and Timer control)
  - `neopixel` (for RGB LED control)
  - `time` (for timing functions)

## Functional Requirements

### 1. Button Operation
- Short press (< 3 seconds): Start normal operation sequence
- Long press (≥ 3 seconds): Enter training mode
- Press during sequence: Cancel current operation

### 2. LED Indicators
- Green (low): Standby/Idle state
- Blue (low): Button pressed
- Green (blinking): Normal operation sequence
- Orange (3 flashes): Training mode save successful
- Red (3 quick flashes): Training mode save failed
- Red (1 second): Operation complete

### 3. Operation Modes

#### Normal Operation
1. Start with short button press
2. Blink green LED for configured duration
3. Switch Pin 5 LOW for 250ms (normally HIGH)
4. Show red LED for 1 second
5. Return to standby (green)

#### Training Mode
1. Enter with long button press
2. Record time between press and release
3. Save timing to configuration file
4. Indicate save status with LED
5. Execute normal completion sequence

### 4. State Management
- IDLE: Default state, waiting for input
- BLINKING: During normal operation sequence
- TRAINING: During training mode

### 5. Configuration
- Timing configuration stored in file system
- Persists across reboots
- Default timing if no configuration present

### 6. Error Handling
- Debounce handled via polling (100ms intervals)
- Clear visual feedback for all operations
- Graceful cancellation of operations
- Recovery to idle state on errors

## Performance Requirements
- Button polling rate: 100ms
- LED blink period: 500ms
- Minimum operation time: 1 second
- Maximum operation time: None specified
- Pin 5 activation time: 250ms (LOW pulse, normally HIGH)
- Completion indicator time: 1 second
