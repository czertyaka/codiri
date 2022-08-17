from .common import log, pasquill_gifford_classes
from typing import Tuple


class BaseInput:
    def __init__(self, item_names: Tuple[str]):
        self.__values = dict.fromkeys(item_names, None)

    def initialized(self) -> bool:
        return all(
            [
                False if item is None else True
                for item in self.__values.values()
            ]
        )

    def valid(self) -> bool:
        raise NotImplementedError

    def __str__(self) -> str:
        return str(self.__values)

    def __getitem__(self, key):
        return self.__values[key]

    def __setitem__(self, key, item):
        if key not in self.__values:
            raise KeyError(f"input has no {key} field")
        self.__values[key] = item


class Input(BaseInput):
    """Holds input data for model"""

    def __init__(self):
        super(Input, self).__init__(
            (
                "distance",
                "square_side",
                "specific_activities",
                "precipitation_rate",
                "extreme_windspeeds",
                "age",
                "terrain_type",
                "blowout_time",
            )
        )

    def valid(self) -> bool:
        return (
            self.distance <= 50000
            and self.distance > (self.square_side / 2)
            and self.age >= 0
        )

    @property
    def distance(self) -> float:
        return self["distance"]

    @distance.setter
    def distance(self, value: float) -> None:
        """Distance between source center and point where doses should be
        calculated, m"""
        self["distance"] = value

    @property
    def square_side(self) -> float:
        return self["square_side"]

    @square_side.setter
    def square_side(self, value: float) -> float:
        """Square-shaped surface source side length, m"""
        self["square_side"] = value

    @property
    def specific_activities(self) -> dict:
        return self["specific_activities"]

    def add_specific_activity(self, nuclide: str, specific_activity: float):
        """Add specific activity for specific nuclide, Bq/kg"""
        prev = self["specific_activities"].get(nuclide)
        self["specific_activities"][nuclide] = (
            (prev + specific_activity)
            if prev is not None
            else specific_activity
        )

    @property
    def precipitation_rate(self) -> float:
        return self["precipitation_rate"]

    @precipitation_rate.setter
    def precipitation_rate(self, value: float):
        """Precipation rate, mm/hr"""
        self["precipitation_rate = value"]

    @property
    def extreme_windspeeds(self) -> dict:
        return self["extreme_windspeeds"]

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
        self["extreme_windspeeds"] = values

    @property
    def age(self) -> int:
        return self["age"]

    @age.setter
    def age(self, value: int) -> None:
        self["age"] = value

    @property
    def terrain_type(self) -> str():
        return self["terrain_type"]

    @terrain_type.setter
    def terrain_type(self, value: str) -> None:
        """Underlying terrain type
        :param value: valid types are "greenland", "agricultural", "forest" and
            "settlement"
        :raises ValueError: unknown terrain type
        """
        if value not in ["greenland", "agricultural", "forest", "settlement"]:
            raise ValueError(f"unknown terrain type '{value}'")
        self["terrain_type"] = value

    @property
    def blowout_time(self) -> int:
        return self["blowout_time"]

    @blowout_time.setter
    def blowout_time(self, value: int) -> None:
        """Wind operation (blowout) time, sec"""
        self["blowout_time"] = value
