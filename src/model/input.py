from .common import log, pasquill_gifford_classes


class Input:
    """Holds input data for model"""

    def __init__(self):
        self.__distance = None
        self.__square_side = None
        self.__specific_activities = dict()
        self.__precipitation_rate = None
        self.__extreme_windspeeds = None
        self.__age = None
        self.__terrain_type = None
        self.__blowout_time = None

    def initialized(self) -> bool:
        return (
            self.distance is not None
            and self.square_side is not None
            and len(self.specific_activities) > 0
            and self.precipitation_rate is not None
            and self.extreme_windspeeds is not None
            and self.age is not None
            and self.terrain_type is not None
            and self.blowout_time is not None
        )

    def valid(self) -> bool:
        return (
            self.distance <= 50000
            and self.distance > (self.square_side / 2)
            and self.age >= 0
        )

    def __str__(self) -> str:
        return str(
            f"{{distance: {self.distance}; square side: {self.square_side};"
            f" age: {self.age}; terrain type: {self.terrain_type}}}"
        )

    @property
    def distance(self) -> float:
        return self.__distance

    @distance.setter
    def distance(self, value: float) -> None:
        """Distance between source center and point where doses should be
        calculated, m"""
        self.__distance = value

    @property
    def square_side(self) -> float:
        return self.__square_side

    @square_side.setter
    def square_side(self, value: float) -> float:
        """Square-shaped surface source side length, m"""
        self.__square_side = value

    @property
    def specific_activities(self) -> dict:
        return self.__specific_activities

    def add_specific_activity(self, nuclide: str, specific_activitiy: float):
        """Add specific activity for specific nuclide, Bq/kg"""
        prev = self.__specific_activities.get(nuclide)
        self.__specific_activities[nuclide] = (
            (prev + specific_activitiy)
            if prev is not None
            else specific_activitiy
        )

    @property
    def precipitation_rate(self) -> float:
        return self.__precipitation_rate

    @precipitation_rate.setter
    def precipitation_rate(self, value: float):
        """Precipation rate, mm/hr"""
        self.__precipitation_rate = value

    @property
    def extreme_windspeeds(self) -> dict:
        return self.__extreme_windspeeds

    @extreme_windspeeds.setter
    def extreme_windspeeds(self, values: dict):
        """Extreme wind speed for each Pasquill-Gifford atmospheric stability
        classes as a list of count 6, m/s"""
        if sorted(values.keys()) != sorted(pasquill_gifford_classes):
            log(
                f"given wind speeds list ({values}) doesn't provide "
                f"necessary atmospheric stability classes "
                f"({pasquill_gifford_classes})"
            )
            return
        self.__extreme_windspeeds = values

    @property
    def age(self) -> int:
        return self.__age

    @age.setter
    def age(self, value: int) -> None:
        self.__age = value

    @property
    def terrain_type(self) -> str():
        return self.__terrain_type

    @terrain_type.setter
    def terrain_type(self, value: str) -> None:
        """Underlying terrain type
        :param value: valid types are "greenland", "agricultural", "forest" and
            "settlement"
        :raises ValueError: unknown terrain type
        """
        if value not in ["greenland", "agricultural", "forest", "settlement"]:
            raise ValueError(f"unknown terrain type '{value}'")
        self.__terrain_type = value

    @property
    def blowout_time(self) -> int:
        return self.__blowout_time

    @blowout_time.setter
    def blowout_time(self, value: int) -> None:
        """Wind operation (blowout) time, sec"""
        self.__blowout_time = value
