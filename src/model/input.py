from .common import pasquill_gifford_classes, ValidatingFixedMap, ValidatingMap
from typing import Dict, Tuple


class Input:
    """Holds input data for model"""

    def __init__(self):
        """Input constructor"""
        self.__values = ValidatingFixedMap(
            (
                "distance",
                "square_side",
                "specific_activities",
                "precipitation_rate",
                "extreme_windspeeds",
                "age",
                "terrain_type",
                "blowout_time",
                "buffer_area_radius",
                "adults_annual_food_intake",
            )
        )
        self.__values["specific_activities"] = (
            ValidatingMap(),
            lambda x: True,
            str(),
        )

    @property
    def values(self):
        return self.__values

    def __str__(self):
        return str(self.__values)

    def initialized(self) -> bool:
        """Check if all fields have values

        Returns:
            bool: check result
        """
        return (
            self.__values.initialized() and len(self.specific_activities) > 0
        )

    @property
    def distance(self) -> float:
        """Get distance between source center and point where doses should be
        calculated

        Returns:
            float: distance, m
        """
        return self.__values["distance"]

    @distance.setter
    def distance(self, value: float):
        """Set distance between source center and point where doses should be
        calculated

        Args:
            value (float): distance, m
        """
        self.__values["distance"] = (
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
        return self.__values["square_side"]

    @square_side.setter
    def square_side(self, value: float) -> float:
        """Set square-shaped surface source side length

        Args:
            value (float): square size length, m
        """
        self.__values["square_side"] = (
            value,
            lambda x: x >= 0,
            f"invalid square side '{value} m'",
        )

    @property
    def specific_activities(self) -> ValidatingMap:
        """Get specific activities of the source

        Returns:
            ValidatingMap: specific activities dictionary, where key is
                nuclide name and value is Bq/kg
        """
        return self.__values["specific_activities"]

    @property
    def nuclides(self) -> Tuple[str]:
        """Get nuclides list

        Returns:
            Tuple[str]: nuclides list
        """
        return tuple(self.__values["specific_activities"].keys())

    def add_specific_activity(self, nuclide: str, specific_activity: float):
        """Add specific activity for a nuclide

        Args:
            nuclide (str): nuclide name
            specific_activity (float): specific activity, Bq/kg
        """
        self.__values["specific_activities"][nuclide] = (
            specific_activity,
            lambda x: x > 0,
            f"invalid specific_activity '{specific_activity} Bq' for "
            f"'{nuclide}'",
        )

    @property
    def precipitation_rate(self) -> float:
        """Get precipation rate

        Returns:
            float: precipation rate, mm/hr
        """
        return self.__values["precipitation_rate"]

    @precipitation_rate.setter
    def precipitation_rate(self, value: float):
        """Set precipation rate

        Args:
            value (float): precipation rate, mm/hr
        """
        self.__values["precipitation_rate"] = (
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
        return self.__values["extreme_windspeeds"]

    @extreme_windspeeds.setter
    def extreme_windspeeds(self, values: Dict[str, float]):
        """Set extreme windspeeds

        Args:
            values (Dict[str, float]): windspeeds dictionary for each
                Pasquill-Gifford atmospheric stability class, m/s
        """
        self.__values["extreme_windspeeds"] = (
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
        return self.__values["age"]

    @age.setter
    def age(self, value: int):
        """Set population group age

        Args:
            value (int): population group age, year
        """
        self.__values["age"] = (
            value,
            lambda x: x >= 0,
            f"invalid age '{value} years'",
        )

    @property
    def terrain_type(self) -> str:
        """Get underlying terrain type

        Returns:
            str: terrain type
        """
        return self.__values["terrain_type"]

    @terrain_type.setter
    def terrain_type(self, value: str):
        """Set underlying terrain type, valid values are "greenland",
            "agricultural", "forest" and "settlement"

        Args:
            value (str): terrain type
        """
        self.__values["terrain_type"] = (
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
        return self.__values["blowout_time"]

    @blowout_time.setter
    def blowout_time(self, value: int):
        """Set wind operation (blowout) time

        Args:
            value (int): time, s
        """
        self.__values["blowout_time"] = (
            value,
            lambda x: x > 0,
            f"invalid wind operation '{value} sec'",
        )

    @property
    def buffer_area_radius(self) -> float:
        """Get buffer area radius

        Returns:
            float: buffer area radius, m
        """
        return self.__values["buffer_area_radius"]

    @buffer_area_radius.setter
    def buffer_area_radius(self, value: float) -> float:
        """Set buffer area radius

        Args:
            value (float): buffer area radius, m
        """
        self.__values["buffer_area_radius"] = (
            value,
            lambda x: x >= 0,
            f"invalid buffer area radius '{value} m'",
        )

    @property
    def adults_annual_food_intake(self) -> Dict[str, float]:
        """Get annual food intake for adults per food category

        Returns:
            Dict[str, float]: adults annual food intake, kg(l)/year
        """
        return self.__values["adults_annual_food_intake"]

    @adults_annual_food_intake.setter
    def adults_annual_food_intake(self, value: Dict[str, float]):
        """Set annual food intake for adults per food category

        Args:
            value (Dict[str, float]): adults annual food intake, kg(l)/year
        """
        categories = sorted(
            ("meat", "milk", "wheat", "cucumbers", "cabbage", "potato")
        )
        self.__values["adults_annual_food_intake"] = (
            value,
            lambda x: sorted(x.keys()) == categories,
            f"invalid food categories '{value.keys()}', should be "
            f"{categories}",
        )
