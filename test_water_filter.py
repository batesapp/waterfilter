import unittest
from unittest.mock import Mock, patch
import time
import sys
from test_mocks import MockPin, MockTimer, MockNeoPixel
from neopixel_colors import (
    Color, OFF, RED_LOW, GREEN_LOW, 
    BLUE_LOW, ORANGE_LOW
)

# Add constants needed from main.py
LED_PIN = 16
BUTTON_PIN = 27
CONTROL_PIN = 5
BUTTON_LONG_PRESS_MS = 2000
BLINK_PERIOD_MS = 500
CONFIG_BLINK_PERIOD_MS = 200
DEFAULT_BLINK_TIME = 50000
PIN5_ON_TIME_MS = 250
RED_SHOW_TIME_MS = 1000

# Mock the modules before importing main
sys.modules['machine'] = Mock()
sys.modules['machine'].Pin = MockPin
sys.modules['machine'].Timer = MockTimer
sys.modules['neopixel'] = Mock()
sys.modules['neopixel'].NeoPixel = MockNeoPixel

# Now import from main
from main import WaterFilter, LEDController

# Create the test class
class TestWaterFilter(unittest.TestCase):
    def setUp(self):
        self.filter = WaterFilter()
        self.current_time = 0
        # Mock time.ticks_ms
        self.original_ticks_ms = time.ticks_ms
        time.ticks_ms = lambda: self.current_time
        
        # Add after the time.ticks_ms mock in setUp
        def mock_ticks_diff(end, start):
            return end - start
        time.ticks_diff = mock_ticks_diff
        
    def simulate_time_ms(self, ms):
        """Helper to simulate time passage"""
        self.current_time += ms
        return self.current_time
        
    def test_initial_state(self):
        """Test initial state of the controller"""
        self.assertEqual(self.filter.state, 'IDLE')
        self.assertEqual(self.filter.pin5.value(), 1)  # Should be HIGH initially
        
    def test_short_press(self):
        """Test short button press starts normal sequence"""
        # Simulate button press
        self.filter.button.value = lambda: 1
        self.filter._handle_button_press(0)
        
        # Verify blue LED on press
        self.assertEqual(self.filter.led.led[0], BLUE_LOW.to_grb())
        
        # Simulate button release after 1 second
        self.filter.button.value = lambda: 0
        self.filter._handle_button_release(1000)
        
        # Verify state changed to BLINKING
        self.assertEqual(self.filter.state, 'BLINKING')
        
    def test_long_press(self):
        """Test long press enters training mode"""
        # Simulate button press
        self.filter.button.value = lambda: 1
        self.filter._handle_button_press(0)
        
        # Simulate time passage (3 seconds)
        self.simulate_time_ms(3000)
        
        # Trigger long press check
        self.filter.long_press_timer.callback(None)
        
        # Verify entered training mode
        self.assertEqual(self.filter.state, 'TRAINING')
        
    def test_cancel_sequence(self):
        """Test canceling an active sequence"""
        # Start a sequence
        self.filter.button.value = lambda: 1
        self.filter._handle_button_press(0)
        self.filter.button.value = lambda: 0
        self.filter._handle_button_release(500)
        
        # Verify sequence started
        self.assertEqual(self.filter.state, 'BLINKING')
        
        # Cancel sequence with button press
        self.filter.button.value = lambda: 1
        self.filter._handle_button_press(1000)
        
        # Verify cancellation
        self.assertTrue(self.filter.canceling)
        self.assertEqual(self.filter.state, 'IDLE')
        
    def test_completion_sequence(self):
        """Test the completion sequence"""
        # Start completion sequence
        self.filter._execute_action()
        
        # Verify Pin 5 was pulsed LOW
        self.assertEqual(self.filter.pin5.value(), 1)  # Should be back to HIGH
        
        # Verify final state
        self.assertEqual(self.filter.state, 'IDLE')
        self.assertEqual(self.filter.led.led[0], GREEN_LOW.to_grb())
        
    @patch('builtins.open')
    def test_training_mode_save(self, mock_open):
        """Test training mode save functionality"""
        # Mock successful file save
        mock_open.return_value.__enter__.return_value.write = Mock()
        
        # Enter training mode
        self.filter.state = 'TRAINING'
        self.filter.button_press_start = 0
        
        # Simulate button release after 5 seconds
        self.filter._handle_button_release(5000)
        
        # Verify save was attempted
        mock_open.assert_called_once()
        
    def test_error_handling(self):
        """Test error recovery"""
        # Simulate an error by forcing invalid state
        self.filter.state = 'INVALID'
        
        # Execute action should recover to IDLE
        self.filter._execute_action()
        self.assertEqual(self.filter.state, 'IDLE')

    def test_led_colors(self):
        """Test LED color states match requirements"""
        # Test idle state (green)
        self.assertEqual(self.filter.led.led[0], GREEN_LOW.to_grb())
        
        # Test button press (blue)
        self.filter.button.value = lambda: 1
        self.filter._handle_button_press(0)
        self.assertEqual(self.filter.led.led[0], BLUE_LOW.to_grb())
        
        # Test completion sequence
        self.filter._execute_action()
        # Should end with green
        self.assertEqual(self.filter.led.led[0], GREEN_LOW.to_grb())

    def test_training_mode_indicators(self):
        """Test training mode LED indicators"""
        with patch('builtins.open') as mock_open:
            mock_open.return_value.__enter__.return_value.write = Mock(return_value=None)
            
            self.filter.state = 'TRAINING'
            self.filter.button_press_start = 0
            
            # Simulate button release
            self.filter._handle_button_release(5000)
            
            # Should flash orange then end in green
            self.assertEqual(self.filter.led.led[0], GREEN_LOW.to_grb())

    def test_timing_requirements(self):
        """Test timing requirements are met"""
        # Test button polling rate
        self.assertEqual(self.filter.button_poll_timer.period, 100)  # 100ms polling
        
        # Test blink period
        self.filter._start_sequence()
        self.assertEqual(self.filter.blink_timer.period, 500)  # 500ms blink period
        
        # Test training mode blink period
        self.filter._start_training_blink()
        self.assertEqual(self.filter.blink_timer.period, 200)  # 200ms rapid blink

    def test_configuration_persistence(self):
        """Test configuration saving and loading"""
        test_duration = 30000  # 30 seconds
        
        # Test saving
        with patch('builtins.open') as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            from main import save_to_file  # Import the function
            save_result = save_to_file(test_duration)
            self.assertTrue(save_result)
            mock_file.write.assert_called_with(str(test_duration))
        
        # Test loading with default
        with patch('builtins.open', side_effect=OSError):
            from main import read_from_file  # Import the function
            duration = read_from_file()
            self.assertEqual(duration, DEFAULT_BLINK_TIME)  # Should return default value

    def test_pin5_behavior(self):
        """Test Pin 5 behavior matches requirements"""
        # Should start HIGH
        self.assertEqual(self.filter.pin5.value(), 1)
        
        # Execute action should pulse LOW then return to HIGH
        self.filter._execute_action()
        self.assertEqual(self.filter.pin5.value(), 1)  # Should end HIGH

    def test_exact_timing(self):
        """Test exact timing requirements"""
        # Mock time.sleep_ms to track sleep durations
        with patch('time.sleep_ms') as mock_sleep:
            self.filter._execute_action()
            
            # Verify PIN5 pulse timing
            mock_sleep.assert_any_call(250)  # PIN5_ON_TIME_MS
            # Verify red LED timing
            mock_sleep.assert_any_call(1000)  # RED_SHOW_TIME_MS

    def test_edge_case_button_timing(self):
        """Test button press timing edge cases"""
        # Test press right at 3 seconds
        self.filter.button.value = lambda: 1
        self.filter._handle_button_press(0)
        self.filter.long_press_timer.trigger()  # Simulate timer check at exactly 3 seconds
        
        # Should still be in IDLE state as it's not over threshold
        self.assertEqual(self.filter.state, 'IDLE')
        
        # Now test just over 3 seconds
        self.simulate_time_ms(3001)
        self.filter.long_press_timer.trigger()
        self.assertEqual(self.filter.state, 'TRAINING')

    def test_rapid_button_presses(self):
        """Test multiple rapid button presses"""
        for i in range(5):  # Simulate 5 rapid presses
            self.filter.button.value = lambda: 1
            self.filter._handle_button_press(i * 50)  # 50ms apart
            self.filter.button.value = lambda: 0
            self.filter._handle_button_release((i * 50) + 25)
        
        # Should handle gracefully and end in IDLE state
        self.assertEqual(self.filter.state, 'IDLE')

    def test_file_system_errors(self):
        """Test file system error conditions"""
        # Test write error
        with patch('builtins.open', side_effect=OSError("Disk full")):
            # Enter training mode
            self.filter.state = 'TRAINING'
            self.filter.button_press_start = 0
            
            # Try to save
            self.filter._handle_button_release(5000)
            
            # Should handle error gracefully
            self.assertEqual(self.filter.state, 'IDLE')
            self.assertEqual(self.filter.led.led[0], GREEN_LOW.to_grb())

    def test_color_handling(self):
        """Test color object handling and conversion"""
        # Test color setting
        self.filter.led.set_color(RED_LOW)
        self.assertEqual(self.filter.led.led[0], RED_LOW.to_grb())
        
        # Test color toggling
        self.filter.led.toggle()
        self.assertEqual(self.filter.led.led[0], OFF.to_grb())
        
        # Test toggle back on
        self.filter.led.toggle()
        self.assertEqual(self.filter.led.led[0], RED_LOW.to_grb())
        
        # Test brightness
        bright_red = Color(255, 0, 0, 1.0)  # Full brightness red
        self.filter.led.set_color(bright_red)
        self.assertEqual(self.filter.led.led[0], (0, 255, 0))  # GRB order
        
        # Test color mixing
        orange = Color(255, 165, 0, 0.25)  # Low brightness orange
        self.filter.led.set_color(orange)
        self.assertEqual(
            self.filter.led.led[0], 
            (int(165 * 0.25), int(255 * 0.25), 0)  # GRB order
        )

    def tearDown(self):
        # Restore original time.ticks_ms
        time.ticks_ms = self.original_ticks_ms

if __name__ == '__main__':
    unittest.main() 