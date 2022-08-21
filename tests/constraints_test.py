from codiri.src.model.constraints import (
    IConstraints,
    ConstraintsComplianceError,
)
from codiri.src.model.input import Input
from codiri.src.model.model import DefaultConstraints
import unittest
from unittest.mock import MagicMock, call


class IContraintsTest(unittest.TestCase):
    def setUp(self):
        self.__constraints = IConstraints()

    def test_init(self):
        inp = Input()
        self.__constraints.validate(inp)

    def test_add_validate(self):
        inp = Input()
        mock = MagicMock(return_value=True)
        self.__constraints.add(mock, lambda inp: "first validator failed")
        self.__constraints.validate(inp)
        mock.assert_called_once_with(inp)
        prev_mock = mock
        mock = MagicMock(return_value=False)
        self.__constraints.add(mock, lambda inp: "second validator failed")
        with self.assertRaisesRegex(
            ConstraintsComplianceError, "second validator failed"
        ):
            self.__constraints.validate(inp)
        prev_mock.assert_has_calls([call(inp), call(inp)])
        mock.assert_called_once_with(inp)


class DefaultConstraintsTest(unittest.TestCase):
    def setUp(self):
        self.__constraints = DefaultConstraints()

    def test_invalid_input(self):
        inp = Input()
        inp.distance = 50001
        inp.square_side = 100
        with self.assertRaisesRegex(
            ConstraintsComplianceError,
            ".*50001([.]0*)? m.*exceeds.*50000([.]0*)? m",
        ):
            self.__constraints.validate(inp)
        inp.distance = 499
        inp.square_side = 1000
        with self.assertRaisesRegex(
            ConstraintsComplianceError,
            ".*499([.]0*)? m.*should exceed.*500([.]0*)? m",
        ):
            self.__constraints.validate(inp)

    def test_valid_input(self):
        inp = Input()
        inp.distance = 49999
        inp.square_side = 99997
        self.__constraints.validate(inp)
