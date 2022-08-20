from .common import pasquill_gifford_classes
from typing import Tuple, Callable, Dict, Any


class FixedMap:
    def __init__(self, keys: Tuple[str]):
        """FixedMap constructor

        Args:
            keys (Tuple[str]): tuple of data fields names
        """
        self.__values = dict.fromkeys(keys, None)

    def initialized(self) -> bool:
        """Check if all fields have values

        Returns:
            bool: check result
        """
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


class ValidatingFixedMap(FixedMap):

    """Summary"""

    def __init__(self, keys: Tuple[str]):
        """Summary

        Args:
            keys (Tuple[str]): Description
        """
        super(ValidatingFixedMap, self).__init__(keys)

    def __setitem__(self, key, item: Tuple[Any, Callable, str]):
        """Summary

        Args:
            key (TYPE): Description
            item (Tuple[Any, Callable, str]): Description

        Raises:
            ValueError: Description
        """
        value = item[0]
        validator = item[1]
        err_msg = item[2]
        if not validator(value):
            raise ValueError(err_msg)
        super(ValidatingFixedMap, self).__setitem__(key, value)


class Input(ValidatingFixedMap):
    """Holds input data for model"""

    def __init__(self):
        """Input constructor"""
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
        self["specific_activities"] = dict(), lambda x: True, str()

    def initialized(self) -> bool:
        """Check if all fields have values

        Returns:
            bool: check result
        """
        return (
            super(Input, self).initialized()
            and len(self.specific_activities) > 0
        )

    @property
    def distance(self) -> float:
        """Get distance between source center and point where doses should be
        calculated

        Returns:
            float: distance, m
        """
        return self["distance"]

    @distance.setter
    def distance(self, value: float):
        """Set distance between source center and point where doses should be
        calculated

        Args:
            value (float): distance, m
        """
        self["distance"] = (
            value,
            lambda x: x >= 0,
            f"invalid distance '{value} m'",
        )

    @property
    def square_side(self) -> float:
        """Get square-shaped surface source side length

        Returns:
            float: square size length, m
        """
        return self["square_side"]

    @square_side.setter
    def square_side(self, value: float) -> float:
        """Set square-shaped surface source side length

        Args:
            value (float): square size length, m
        """
        self["square_side"] = (
            value,
            lambda x: x >= 0,
            f"invalid square side '{value} m'",
        )

    @property
    def specific_activities(self) -> Dict[str, float]:
        """Get specific activities of the source

        Returns:
            Dict[str, float]: specific activities dictionary, where key is
                nuclide name and value is Bq/kg
        """
        return self["specific_activities"]

    def add_specific_activity(self, nuclide: str, specific_activity: float):
        """Add specific activity for a nuclide

        Args:
            nuclide (str): nuclide name
            specific_activity (float): specific activity, Bq/kg

        Raises:
            ValueError: specific activity validation failed
        """
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
        """Get precipation rate

        Returns:
            float: precipation rate, mm/hr
        """
        return self["precipitation_rate"]

    @precipitation_rate.setter
    def precipitation_rate(self, value: float):
        """Set precipation rate

        Args:
            value (float): precipation rate, mm/hr
        """
        self["precipitation_rate"] = (
            value,
            lambda x: x >= 0,
            f"invalid precipitation rate '{value} mm/hr'",
        )

    @property
    def extreme_windspeeds(self) -> Dict[str, float]:
        """Get extreme windspeeds

        Returns:
            Dict[str, float]: windspeeds dictionary for each Pasquill-Gifford
                atmospheric stability class, m/s
        """
        return self["extreme_windspeeds"]

    @extreme_windspeeds.setter
    def extreme_windspeeds(self, values: Dict[str, float]):
        """Set extreme windspeeds

        Args:
            values (Dict[str, float]): windspeeds dictionary for each
                Pasquill-Gifford atmospheric stability class, m/s
        """
        self["extreme_windspeeds"] = (
            values,
            lambda x: sorted(x.keys()) == sorted(pasquill_gifford_classes),
            f"given wind speeds list ({values}) doesn't provide necessary "
            f"atmospheric stability classes ({pasquill_gifford_classes})",
        )

    @property
    def age(self) -> int:
        """Get population group age

        Returns:
            int: population group age, year
        """
        return self["age"]

    @age.setter
    def age(self, value: int):
        """Set population group age

        Args:
            value (int): population group age, year
        """
        self["age"] = value, lambda x: x >= 0, f"invalid age '{value} years'"

    @property
    def terrain_type(self) -> str:
        """Get underlying terrain type

        Returns:
            str: terrain type
        """
        return self["terrain_type"]

    @terrain_type.setter
    def terrain_type(self, value: str):
        """Set underlying terrain type, valid values are "greenland",
            "agricultural", "forest" and "settlement"

        Args:
            value (str): terrain type
        """
        self["terrain_type"] = (
            value,
            lambda x: x
            in ["greenland", "agricultural", "forest", "settlement"],
            f"unknown terrain type '{value}'",
        )

    @property
    def blowout_time(self) -> int:
        """Get wind operation (blowout) time

        Returns:
            int: time, s
        """
        return self["blowout_time"]

    @blowout_time.setter
    def blowout_time(self, value: int):
        """Set wind operation (blowout) time

        Args:
            value (int): time, s
        """
        self["blowout_time"] = (
            value,
            lambda x: x > 0,
            f"invalid wind operation '{value} sec'",
        )
