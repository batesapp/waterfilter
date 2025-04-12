from neopixel_colors import Color, OFF

class MockPin:
    IN = 'IN'
    OUT = 'OUT'
    PULL_DOWN = 'PULL_DOWN'
    
    def __init__(self, pin_num, direction=None, pull=None):
        self._value = 0
        self.pin_num = pin_num
        self.direction = direction
        self.pull = pull
    
    def value(self, val=None):
        if val is not None:
            self._value = val
        return self._value

class MockTimer:
    PERIODIC = 'PERIODIC'
    ONE_SHOT = 'ONE_SHOT'
    
    def __init__(self):
        self.callback = None
        self.period = None
        self.mode = None
        
    def init(self, period=None, mode=None, callback=None):
        self.period = period
        self.mode = mode
        self.callback = callback
        
    def deinit(self):
        self.callback = None

    def trigger(self):
        """Simulate timer trigger"""
        if self.callback:
            self.callback(self)

class MockNeoPixel:
    def __init__(self, pin, num_leds):
        self.pin = pin
        self.num_leds = num_leds
        self.leds = [OFF.to_grb()] * num_leds
        
    def __getitem__(self, index):
        return self.leds[index]
        
    def __setitem__(self, index, value):
        if isinstance(value, Color):
            self.leds[index] = value.to_grb()
        else:
            self.leds[index] = value
        
    def write(self):
        pass

class MockLEDController:
    def __init__(self, pin_num):
        self.led = MockNeoPixel(pin_num, 1)
        self.current_color = GREEN_LOW
        self.is_on = True
        
    def set_color(self, color):
        self.current_color = color
        self.led[0] = color
        self.led.write()
        self.is_on = True
        
    def turn_off(self):
        self.led[0] = OFF
        self.led.write()
        self.is_on = False 