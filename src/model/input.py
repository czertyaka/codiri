from .common import pasquill_gifford_classes
from typing import Tuple, Callable


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
        self.__set_value("specific_activities", dict())

    def initialized(self) -> bool:
        return (
            super(Input, self).initialized()
            and len(self.specific_activities) > 0
        )

    def __set_value(
        self, key, item, validator: Callable = lambda x: True, err_msg=""
    ):
        if not validator(item):
            raise ValueError(err_msg)
        self[key] = item

    @property
    def distance(self) -> float:
        return self["distance"]

    @distance.setter
    def distance(self, value: float) -> None:
        """Distance between source center and point where doses should be
        calculated, m"""
        self.__set_value(
            "distance",
            value,
            lambda x: x >= 0,
            f"invalid distance '{value} m'",
        )

    @property
    def square_side(self) -> float:
        return self["square_side"]

    @square_side.setter
    def square_side(self, value: float) -> float:
        """Square-shaped surface source side length, m"""
        self.__set_value(
            "square_side",
            value,
            lambda x: x >= 0,
            f"invalid square side '{value} m'",
        )

    @property
    def specific_activities(self) -> dict:
        return self["specific_activities"]

    def add_specific_activity(self, nuclide: str, specific_activity: float):
        """Add specific activity for specific nuclide, Bq/kg"""
        if specific_activity < 0:
            raise ValueError(
                f"invalid specific activity '{specific_activity} Bq/kg'"
            )
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
        self.__set_value(
            "precipitation_rate",
            value,
            lambda x: x >= 0,
            f"invalid precipitation rate '{value} mm/hr'",
        )

    @property
    def extreme_windspeeds(self) -> dict:
        return self["extreme_windspeeds"]

    @extreme_windspeeds.setter
    def extreme_windspeeds(self, values: dict):
        """Extreme wind speed for each Pasquill-Gifford atmospheric stability
        classes as a list of count 6, m/s"""
        self.__set_value(
            "extreme_windspeeds",
            values,
            lambda x: sorted(x.keys()) == sorted(pasquill_gifford_classes),
            f"given wind speeds list ({values}) doesn't provide "
            f"necessary atmospheric stability classes "
            f"({pasquill_gifford_classes})",
        )

    @property
    def age(self) -> int:
        return self["age"]

    @age.setter
    def age(self, value: int) -> None:
        """Control group age, years"""
        self.__set_value(
            "age", value, lambda x: x >= 0, f"invalid age '{value} years'"
        )

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
        self.__set_value(
            "terrain_type",
            value,
            lambda x: x
            in ["greenland", "agricultural", "forest", "settlement"],
            f"unknown terrain type '{value}'",
        )

    @property
    def blowout_time(self) -> int:
        return self["blowout_time"]

    @blowout_time.setter
    def blowout_time(self, value: int) -> None:
        """Wind operation (blowout) time, sec"""
        self.__set_value(
            "blowout_time",
            value,
            lambda x: x > 0,
            f"invalid wind operation '{value} sec'",
        )
