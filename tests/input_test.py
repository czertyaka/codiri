from codiri.src.model.input import Input
import unittest


class TestInput(unittest.TestCase):
    def test_input_init(self):
        values = Input().values
        self.assertEqual(values["distance"], None)
        self.assertEqual(values["square_side"], None)
        self.assertEqual(values["precipitation_rate"], None)
        self.assertEqual(values["extreme_windspeeds"], None)
        self.assertEqual(values["age"], None)
        self.assertEqual(values["terrain_type"], None)
        self.assertEqual(values["blowout_time"], None)
        self.assertEqual(values["buffer_area_radius"], None)
        self.assertEqual(values["adults_annual_food_intake"], None)

        self.assertEqual(str(values["specific_activities"]), "{}")

    def test_input_simple_setters(self):
        inp = Input()
        with self.assertRaises(ValueError):
            inp.distance = -1
        with self.assertRaises(ValueError):
            inp.square_side = -1
        with self.assertRaises(ValueError):
            inp.precipitation_rate = -1
        with self.assertRaises(ValueError):
            inp.age = -1
        with self.assertRaises(ValueError):
            inp.blowout_time = -1
        with self.assertRaises(ValueError):
            inp.blowout_time = 0
        with self.assertRaises(ValueError):
            inp.buffer_area_radius = -1

    def test_input_extreme_windspeeds(self):
        inp = Input()
        with self.assertRaises(ValueError):
            inp.extreme_windspeeds = {}
        with self.assertRaises(ValueError):
            inp.extreme_windspeeds = {"1": 1}
        inp.extreme_windspeeds = {
            "A": 1,
            "B": 1,
            "C": 1,
            "D": 1,
            "E": 1,
            "F": 1,
        }

    def test_input_terrain_type(self):
        inp = Input()
        inp.terrain_type = "greenland"
        inp.terrain_type = "agricultural"
        inp.terrain_type = "forest"
        inp.terrain_type = "settlement"
        with self.assertRaises(ValueError):
            inp.terrain_type = "invalid"

    def test_input_adults_annual_food_intake(self):
        inp = Input()
        inp.adults_annual_food_intake = {
            "meat": 1,
            "milk": 2,
            "wheat": 3,
            "cucumbers": 4,
            "cabbage": 5,
            "potato": 6,
        }
        inp.adults_annual_food_intake = {
            "milk": 1,
            "meat": 2,
            "wheat": 3,
            "cucumbers": 4,
            "cabbage": 5,
            "potato": 6,
        }
        with self.assertRaises(ValueError):
            inp.adults_annual_food_intake = {
                "milk": 1,
                "meat": 2,
                "wheat": 3,
                "cucumbers": 4,
                "cabbage": 5,
                "potato": 6,
                "carrot": 7,
            }
        with self.assertRaises(ValueError):
            inp.adults_annual_food_intake = {
                "milk": 1,
                "meat": 2,
                "wheat": 3,
                "cucumbers": 4,
                "cabbage": 5,
            }

    def test_input_initalized(self):
        inp = Input()
        self.assertFalse(inp.initialized())
        inp.distance = 1
        inp.square_side = 1
        inp.precipitation_rate = 1
        inp.extreme_windspeeds = {
            "A": 1,
            "B": 1,
            "C": 1,
            "D": 1,
            "E": 1,
            "F": 1,
        }
        inp.age = 1
        inp.terrain_type = "greenland"
        inp.buffer_area_radius = 0
        inp.blowout_time = 1
        inp.adults_annual_food_intake = {
            "meat": 1,
            "milk": 2,
            "wheat": 3,
            "cucumbers": 4,
            "cabbage": 5,
            "potato": 6,
        }
        self.assertFalse(inp.initialized())
        inp.add_specific_activity("Cs-137", 1)
        self.assertEqual(inp.nuclides, ("Cs-137",))
        self.assertTrue(inp.initialized())
