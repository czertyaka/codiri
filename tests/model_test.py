from codiri.src.model.model import Model
from codiri.src.model.constraints import ConstraintsComplianceError
from codiri.src.model.reference import IReference
from codiri.src.model.input import Input
from unittest.mock import MagicMock
import unittest


class FakeReference(IReference):
    def _initialize_data(self):
        pass


class FakeInput(Input):
    def __init__(self):
        super(FakeInput, self).__init__()
        self.distance = 1
        self.square_side = 1
        self.precipitation_rate = 1
        self.extreme_windspeeds = {
            "A": 1,
            "B": 1,
            "C": 1,
            "D": 1,
            "E": 1,
            "F": 1,
        }
        self.age = 1
        self.terrain_type = "greenland"
        self.blowout_time = 1
        self.buffer_area_radius = 0
        self.add_specific_activity("Cs-137", 1)


class ModelTest(Model):
    def __init__(self, reference: IReference):
        super(ModelTest, self).__init__(reference)

    @property
    def constraints(self):
        return self._constraints

    @property
    def reference(self):
        return self._reference


class TestModelInit(unittest.TestCase):
    def test_no_reference(self):
        with self.assertRaises(ValueError):
            ModelTest(None)

    def test_positive(self):
        reference = FakeReference()
        model = ModelTest(reference)
        self.assertEqual(model.reference, reference)
        self.assertTrue(model.constraints is not None)


class TestModelValidateInput(unittest.TestCase):
    def setUp(self):
        self.model = ModelTest(FakeReference())

    def test_no_input(self):
        self.assertFalse(self.model.validate_input(None))

    def test_empty_input(self):
        self.assertFalse(self.model.validate_input(Input()))

    def test_no_constraints_compliance(self):
        self.model.constraints.validate = MagicMock(
            side_effect=ConstraintsComplianceError()
        )
        self.assertFalse(self.model.validate_input(FakeInput()))

    def test_positive(self):
        self.model.constraints.validate = MagicMock(return_value=None)
        self.assertTrue(self.model.validate_input(FakeInput()))
