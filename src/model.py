from .database import Database, InMemoryDatabase


def _log(msg):
    print("RB-134-17: " + msg)


class _Data:
    """Holds datasets required by model"""

    def __init__(self, dbname):
        self.__reference = Database(dbname)
        self.__results = InMemoryDatabase()

    @property
    def reference(self):
        return self.__reference

    @property
    def results(self):
        return self.__results


class _Input:
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
            _log(f"given distance ({value/1000} km) exceeds maximum (50 km)")
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
            _log(
                f"given wind speeds list ({values}) doesn't provide "
                f"necessary atmospheric stability classes "
                f"({pasquill_gifford_classes})"
            )
            return
        self.__extreme_windspeeds = values


class Model:
    """Doses & dilution factor calculator based on 2 scenario in Руководство
    по безопасности при использовании атомной энергии «Рекомендуемые методы
    оценки и прогнозирования радиационных последствий аварий на объектах
    ядерного топливного цикла (РБ-134-17)"""

    def __init__(self, reference_data_db_name):
        self.__data = _Data(reference_data_db_name)
        self.__input = _Input()

    @property
    def input(self):
        return self.__input

    def reset(self):
        self.__data.results.drop_all()
        self.__input = _Input()

    def calculate(self):
        if self.__is_ready() is False:
            _log("model instance is not ready for calculation")
            return
        pass

    def __is_ready(self):
        return self.__input.initialized() and self.__input.consistent()
