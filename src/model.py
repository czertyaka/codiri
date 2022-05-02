def _log(msg):
    print("RB-134-17: " + msg)


class Model:
    """Doses & dilution factor calculator based on 2 scenario in Руководство
    по безопасности при использовании атомной энергии «Рекомендуемые методы
    оценки и прогнозирования радиационных последствий аварий на объектах
    ядерного топливного цикла (РБ-134-17)"""

    def __init__(self):
        self.distance = None
        self.square_side = None
        self.activities = None
        self.precipation_rate = None
        self.extreme_windspeeds = None

    def reset(self):
        self.__init__()

    @property
    def distance(self):
        return self.__distance

    @distance.setter
    def distance(self, value):
        """Distance between source center and point where doses should be
        calculated, m"""
        if value > 50000:
            _log(f"given distance ({value/1000} km) exceeds maximum (50 km)")
            return
        self.distance = value

    @property
    def square_side(self):
        return self.__square_side

    @square_side.setter
    def square_side(self, value):
        """Square-shaped surface source side length, m"""
        self.square_side = value

    @property
    def activities(self):
        return self.__activities

    def add_activity(self, nuclide, activity):
        """Add accidental release activity for specific nuclide, Bq"""
        # if not db.find_nuclide(nuclide):
        #     _log(f"unknown nuclide {nuclide}")
        #     return
        if self.activities is None:
            self.activities = list()
        self.activities.append(dict(nuclide=nuclide, activity=activity))

    @property
    def precipation_rate(self):
        return self.__precipation_rate

    @precipation_rate.setter
    def precipation_rate(self, value):
        """Precipation rate, mm/hr"""
        self.precipation_rate = value

    @property
    def extreme_windspeeds(self):
        return self.__extreme_windspeeds

    @extreme_windspeeds.setter
    def extreme_windspeeds(self, values):
        """Extreme wind speed for each Pasquill-Gifford atmospheric stability
        classes, m/s"""
        pasquill_gifford_classes = ["A", "B", "C", "D", "E", "F"]
        if sorted(values) != pasquill_gifford_classes:
            _log(
                f"given wind speeds dictionary ({values}) doesn't provide "
                f"necessary atmospheric stability classes "
                f"({pasquill_gifford_classes})"
            )
            return
        self.extreme_windspeeds = values

    def __is_ready(self):
        return (
            self.distance is not None
            and self.square_side is not None
            and self.activities is not None
            and self.precipation_rate is not None
            and self.extreme_windspeeds is not None
            and self.__check_parameters_consistency()
        )

    def __check_parameters_consistency(self):
        return self.distance > (self.square_side / 2)
