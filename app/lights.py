from gpiozero import LED


class Light:
    r = LED(25, initial_value=False)
    g = LED(26, initial_value=False)
    y = LED(24, initial_value=False)

    @staticmethod
    def red(state=False):
        """ controls the red light (pin 26). True == on """
        Light.r.off() if not state else Light.r.on()

    @staticmethod
    def green(state=False):
        """ controls the green light (pin 25). True == on """
        Light.g.off() if not state else Light.g.on()

    @staticmethod
    def yellow(state=False):
        """ controls the buzzer (pin 24). True == on """
        Light.y.off() if not state else Light.y.on()

    @staticmethod
    def set_all(red=False, green=False, yellow=False):
        """ controls all three pins. True == on """
        Light.red(red)
        Light.green(green)
        Light.yellow(yellow)
