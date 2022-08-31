from typing import Tuple, Callable, Any, TypeVar


def log(msg):
    print("model: " + msg)


pasquill_gifford_classes = ("A", "B", "C", "D", "E", "F")


class MapImpl:

    """Simple dictionary proxy constructed from keys only"""

    def __init__(self, keys: Tuple[Any] = tuple()):
        """Constructor

        Args:
            keys (Tuple[Any], optional): dictionary keys
        """
        self.__values = dict.fromkeys(keys, None)

    def __iter__(self):
        return self.__values.__iter__()

    def __setitem__(self, key, value):
        self.__values[key] = value

    def __getitem__(self, key):
        return self.__values[key]

    def __str__(self) -> str:
        return str(self.__values)

    def __repr__(self) -> str:
        return self.__values.__repr__()

    def __len__(self) -> int:
        return len(self.__values)

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


class FixedMap:

    """Dictionary without adding new keys"""

    def __init__(self, keys: Tuple[Any], map_type: TypeVar = MapImpl):
        """FixedMap constructor

        Args:
            keys (Tuple[Any]): dictionary keys
            map_type (TypeVar, optional): implementation type
        """
        self.__values = map_type(keys)

    def __iter__(self):
        return self.__values.__iter__()

    def __getitem__(self, key):
        return self.__values[key]

    def __setitem__(self, key, item):
        if key not in self.__values:
            raise KeyError(f"input has no '{key}'' field")
        self.__values[key] = item

    def __str__(self) -> str:
        return self.__values.__str__()

    def __repr__(self) -> str:
        return self.__values.__repr__()

    def __len__(self) -> int:
        return len(self.__values)

    def initialized(self) -> bool:
        """Check if all fields have values

        Returns:
            bool: check result
        """
        return self.__values.initialized()


class ValidatingMap:

    """Dictionary encouraging to validate inserted values"""

    def __init__(
        self, keys: Tuple[Any] = tuple(), map_type: TypeVar = MapImpl
    ):
        """ValidatingMap constructor

        Args:
            keys (Tuple[Any]): dictionary keys
            map_type (TypeVar, optional): implementation type
        """
        self.__values = map_type(keys)

    def __iter__(self):
        return self.__values.__iter__()

    def __getitem__(self, key):
        return self.__values[key]

    def __setitem__(self, key, item: Tuple[Any, Callable, str]):
        """Insert an element

        Args:
            key (TYPE): key
            item (Tuple[Any, Callable, str]): tuple consisting of an inserted
                value, validator and error message

        Raises:
            ValueError: validation failed
        """
        value = item[0]
        validator = item[1]
        err_msg = item[2]
        if not validator(value):
            raise ValueError(err_msg)
        self.__values[key] = value

    def __str__(self) -> str:
        return self.__values.__str__()

    def __repr__(self) -> str:
        return self.__values.__repr__()

    def __len__(self) -> int:
        return len(self.__values)

    def initialized(self) -> bool:
        """Check if all fields have values

        Returns:
            bool: check result
        """
        return self.__values.initialized()


class ValidatingFixedMap(ValidatingMap):

    """Dictionary combining properties of FixedMap and ValidatingMap"""

    def __init__(self, keys: Tuple[Any]):
        """ValidatingFixedMap constructor

        Args:
            keys (Tuple[Any]): dictionary keys
        """
        super(ValidatingFixedMap, self).__init__(keys, FixedMap)
