from .input import Input
from typing import Callable


class ConstraintsComplianceError(Exception):

    """Failed input validation error"""

    pass


class IConstraints:

    """Input constraints classes interface"""

    def __init__(self):
        """IConstraints constructor"""
        self.__constraints = list()

    def validate(self, inp: Input):
        """Validate input

        Args:
            inp (Input): input

        Raises:
            ConstraintsComplianceError: validation failed
        """
        for constraint in self.__constraints:
            validator = constraint[0]
            if not validator(inp):
                err_msg = constraint[1](inp)
                raise ConstraintsComplianceError(err_msg)

    def add(
        self,
        validator: Callable[
            [
                Input,
            ],
            bool,
        ],
        err_msg_cb: Callable[
            [
                Input,
            ],
            str,
        ] = lambda inp: str(),
    ):
        """Add constraint

        Args:
            validator (Callable[[Input, ], bool, ]): constraint's validator
                callback
            err_msg_cb (Callable[[Input, ], str, ], optional): error message
                callback
        """
        self.__constraints.append((validator, err_msg_cb))
