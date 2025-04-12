class Color:
    """RGB Color representation with brightness control"""
    def __init__(self, red, green, blue, brightness=1.0):
        self.red = min(255, max(0, red))
        self.green = min(255, max(0, green))
        self.blue = min(255, max(0, blue))
        self.brightness = min(1.0, max(0.0, brightness))
    
    def __eq__(self, other):
        if not isinstance(other, (Color, tuple)):
            return False
        if isinstance(other, tuple):
            return (self.green, self.red, self.blue) == other  # GRB order
        return (self.red == other.red and 
                self.green == other.green and 
                self.blue == other.blue and 
                self.brightness == other.brightness)
    
    def to_grb(self):
        """Convert to GRB tuple with applied brightness"""
        return (
            int(self.green * self.brightness),
            int(self.red * self.brightness),
            int(self.blue * self.brightness)
        )

# Predefined colors
OFF = Color(0, 0, 0)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
ORANGE = Color(255, 165, 0)

# Low brightness versions (25%)
RED_LOW = Color(255, 0, 0, 0.25)
GREEN_LOW = Color(0, 255, 0, 0.25)
BLUE_LOW = Color(0, 0, 255, 0.25)
ORANGE_LOW = Color(255, 165, 0, 0.25) 