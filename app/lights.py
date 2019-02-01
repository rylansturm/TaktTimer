from gpiozero import LED


class Light:
    r = LED(25, initial_value=True)
    g = LED(26, initial_value=True)
    b = LED(4, initial_value=True)

    @staticmethod
    def red(state=False):
        """ controls the red light (pin 25). True == on """
        Light.r.on() if state else Light.r.on()

    @staticmethod
    def green(state=False):
        """ controls the green light (pin 26). True == on """
        Light.g.on() if state else Light.g.on()

    @staticmethod
    def buzzer(state=False):
        """ controls the buzzer (pin 4). True == on """
        Light.b.on() if state else Light.b.on()

    @staticmethod
    def set_all(red=False, green=False, buzzer=False):
        """ controls all three pins. True == on """
        Light.red(red)
        Light.green(green)
        Light.buzzer(buzzer)
