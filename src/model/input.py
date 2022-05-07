from .common import log


class Input:
    """Holds input data for model"""

    def __init__(self):
        self.__distance = None
        self.__square_side = None
        self.__activities = list()
        self.__precipation_rate = None
        self.__extreme_windspeeds = None

    def initialized(self):
        return (
            self.distance is not None
            and self.square_side is not None
            and self.activities.count() > 0
            and self.precipation_rate is not None
            and self.extreme_windspeeds is not None
        )

    def consistent(self):
        return self.distance > (self.square_side / 2)

    @property
    def distance(self):
        return self.__distance

    @distance.setter
    def distance(self, value):
        """Distance between source center and point where doses should be
        calculated, m"""
        if value > 50000:
            log(f"given distance ({value/1000} km) exceeds maximum (50 km)")
            return
        self.__distance = value

    @property
    def square_side(self):
        return self.__square_side

    @square_side.setter
    def square_side(self, value):
        """Square-shaped surface source side length, m"""
        self.__square_side = value

    @property
    def activities(self):
        return self.__activities

    def add_activity(self, nuclide, activity):
        """Add accidental release activity for specific nuclide, Bq"""
        self.__activities.append(dict(nuclide=nuclide, activity=activity))

    @property
    def precipation_rate(self):
        return self.__precipation_rate

    @precipation_rate.setter
    def precipation_rate(self, value):
        """Precipation rate, mm/hr"""
        self.__precipation_rate = value

    @property
    def extreme_windspeeds(self):
        return self.__extreme_windspeeds

    @extreme_windspeeds.setter
    def extreme_windspeeds(self, values):
        """Extreme wind speed for each Pasquill-Gifford atmospheric stability
        classes as a list of count 6, m/s"""
        pasquill_gifford_classes = ["A", "B", "C", "D", "E", "F"]
        if values.count() != 6:
            log(
                f"given wind speeds list ({values}) doesn't provide "
                f"necessary atmospheric stability classes "
                f"({pasquill_gifford_classes})"
            )
            return
        self.__extreme_windspeeds = values
