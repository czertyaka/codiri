from codiri.src.model.model import Model
from codiri.src.model.results import Results
from codiri.src.model.reference import IReference
from codiri.src.database import InMemoryDatabase
from codiri.src.model.input import BaseInput, Input
import math
from unittest.mock import MagicMock, patch
import pytest
import unittest


class TestBaseInput(unittest.TestCase):
    def test_base_input_init(self):
        self.assertEqual(BaseInput(())._BaseInput__values, dict())
        self.assertEqual(BaseInput(("1"))._BaseInput__values, {"1": None})
        self.assertEqual(
            BaseInput(("1", "2"))._BaseInput__values, {"1": None, "2": None}
        )

    def test_base_input_initialized(self):
        inp = BaseInput(("1", "2"))
        self.assertFalse(inp.initialized())
        inp["1"] = 1
        self.assertFalse(inp.initialized())
        inp["2"] = 2
        self.assertTrue(inp.initialized())

    def test_base_input_str(self):
        self.assertEqual(str(BaseInput(())), "{}")
        self.assertEqual(str(BaseInput(("1"))), "{'1': None}")
        self.assertEqual(str(BaseInput(("1", "2"))), "{'1': None, '2': None}")
        inp = BaseInput(["1", "2"])
        inp["1"] = 1
        inp["2"] = 2
        self.assertEqual(str(inp), "{'1': 1, '2': 2}")

    def test_base_input_setitem(self):
        inp = BaseInput(("1", "2"))
        with self.assertRaises(KeyError):
            inp["0"] = 0
        self.assertEqual(inp["1"], None)
        inp["1"] = 1
        self.assertEqual(inp["1"], 1)

    def test_base_input_valid(self):
        with self.assertRaises(NotImplementedError):
            BaseInput(()).valid()
        with self.assertRaises(NotImplementedError):
            BaseInput(("1", "2")).valid()


class ReferenceTest(IReference):
    def __init__(self):
        super(ReferenceTest, self).__init__()
        self.__db = InMemoryDatabase()

    @property
    def db(self):
        return self.__db

    @property
    def dose_rate_decay_coeff(self) -> float:
        return 0.5

    @property
    def residence_time(self) -> float:
        return -math.log(2)

    @property
    def unitless_washing_capacity(self) -> float:
        return 2

    def standard_washing_capacity(self, nuclide: str) -> float:
        return 3

    @property
    def terrain_clearance(self) -> float:
        return 1

    @property
    def mixing_layer_height(self) -> float:
        return 1

    def terrain_roughness(self, terrain_type: str) -> float:
        return 1


class ModelTest(Model):
    def __init__(self):
        self._Model__results = Results()
        self.__reference = ReferenceTest()

    @property
    def reference(self):
        return self.__reference


def test_calculate_e_max_10():
    model = ModelTest()
    e_total_10_table = model.results.e_total_10
    e_total_10_table.insert("A-0", dict(A=0, B=6, C=2, D=8, E=4, F=10))
    e_total_10_table.insert("B-1", dict(A=1, B=7, C=3, D=9, E=5, F=11))

    model._Model__calculate_e_max_10()

    assert model.results.e_max_10 == 21


def test_calculate_e_total_10():
    model = ModelTest()

    e_cloud_table = model.results.e_cloud
    e_inh_table = model.results.e_inhalation
    e_surface_table = model.results.e_surface

    model.reference.db["nuclides"].insert(dict(name="A-0", group="aerosol"))
    e_cloud_table.insert("A-0", dict(A=0, B=6, C=2, D=8, E=4, F=10))
    e_inh_table.insert("A-0", dict(A=1, B=7, C=3, D=9, E=5, F=11))
    e_surface_table.insert("A-0", dict(A=2, B=8, C=4, D=10, E=6, F=12))

    model.reference.db["nuclides"].insert(dict(name="B-1", group="IRG"))
    e_cloud_table.insert("B-1", dict(A=0, B=6, C=2, D=8, E=4, F=10))
    e_inh_table.insert("B-1", dict(A=1, B=7, C=3, D=9, E=5, F=11))
    e_surface_table.insert("B-1", dict(A=2, B=8, C=4, D=10, E=6, F=12))

    model._Model__calculate_e_total_10("A-0")
    model._Model__calculate_e_total_10("B-1")

    e_total_10_table = model.results.e_total_10
    assert e_total_10_table["A-0"] == dict(A=3, B=21, C=9, D=27, E=15, F=33)
    assert e_total_10_table["B-1"] == dict(A=0, B=6, C=2, D=8, E=4, F=10)


def test_calculate_e_cloud():
    model = ModelTest()

    model.reference.db["nuclides"].insert(dict(name="A-0", R_cloud=1.5))
    model.results.concentration_integrals.insert(
        "A-0", dict(A=0, B=6, C=2, D=8, E=4, F=10)
    )

    model._Model__calculate_e_cloud("A-0")

    assert model.results.e_cloud["A-0"] == dict(A=0, B=9, C=3, D=12, E=6, F=15)


def test_calculate_e_inh():
    model = ModelTest()

    model.reference.db["nuclides"].insert(dict(name="A-0", R_inh=1.5))
    model.reference.db["age_groups"].insert(
        dict(id=0, lower_age=0, upper_age=10, respiration_rate=1)
    )
    model.reference.db["age_groups"].insert(
        dict(id=1, lower_age=10, upper_age=20, respiration_rate=2)
    )

    model.results.concentration_integrals.insert(
        "A-0", dict(A=0, B=6, C=2, D=8, E=4, F=10)
    )

    input = Input()
    input.age = 5
    model.input = input
    model._Model__calculate_e_inh("A-0")

    assert model.results.e_inhalation["A-0"] == dict(
        A=0, B=9, C=3, D=12, E=6, F=15
    )

    input.age = 15
    model.input = input
    model._Model__calculate_e_inh("A-0")

    assert model.results.e_inhalation["A-0"] == dict(
        A=0, B=18, C=6, D=24, E=12, F=30
    )


def test_calculate_residence_time_coeff():
    model = ModelTest()

    model.reference.db["nuclides"].insert(dict(name="A-0", decay_coeff=0.5))

    assert model._Model__calculate_residence_time_coeff("A-0") == -1


def test_calculate_e_surface():
    model = ModelTest()

    model._Model__calculate_residence_time_coeff = MagicMock(return_value=1)
    model.reference.db["nuclides"].insert(dict(name="A-0", R_surface=2))
    model.results.depositions.insert(
        "A-0", dict(A=0, B=6, C=2, D=8, E=4, F=10)
    )

    model._Model__calculate_e_surface("A-0")

    assert model.results.e_surface["A-0"] == dict(
        A=0, B=12, C=4, D=16, E=8, F=20
    )


def test_calculate_depositions():
    model = ModelTest()

    model.reference.db["nuclides"].insert(dict(name="A-0", deposition_rate=1))
    model.results.sediment_detachments.insert("A-0", 2)
    model.results.concentration_integrals.insert(
        "A-0", dict(A=0, B=6, C=2, D=8, E=4, F=10)
    )
    model.results.height_concentration_integrals.insert(
        "A-0", dict(A=1, B=7, C=3, D=9, E=5, F=11)
    )

    model._Model__calculate_depositions("A-0")

    assert model.results.depositions["A-0"] == dict(
        A=2, B=20, C=8, D=26, E=14, F=32
    )


def test_calculate_height_concentration_integrals():
    model = ModelTest()

    input = Input()
    activity = 2
    input.add_specific_activity("A-0", activity)
    input.extreme_windspeeds = dict(A=1, B=1, C=1, D=1, E=1, F=1)
    model.input = input

    model.results.height_deposition_factors.insert(
        "A-0", dict(A=0, B=6, C=2, D=8, E=4, F=10)
    )

    with patch("codiri.src.model.model.blowout_activity_flow") as mocked:
        mocked.return_value = activity
        model._Model__calculate_height_concentration_integrals("A-0")

    assert model.results.height_concentration_integrals["A-0"] == dict(
        A=0, B=12, C=4, D=16, E=8, F=20
    )


def test_calculate_concentration_integrals():
    model = ModelTest()

    input = Input()
    activity = 2
    input.add_specific_activity("A-0", activity)
    input.extreme_windspeeds = dict(A=1, B=1, C=1, D=1, E=1, F=1)
    model.input = input

    model.results.dilution_factors.insert(
        "A-0", dict(A=0, B=6, C=2, D=8, E=4, F=10)
    )

    with patch("codiri.src.model.model.blowout_activity_flow") as mocked:
        mocked.return_value = activity
        model._Model__calculate_concentration_integrals("A-0")

    assert model.results.concentration_integrals["A-0"] == dict(
        A=0, B=12, C=4, D=16, E=8, F=20
    )


def test_calculate_sediment_detachments():
    model = ModelTest()

    input = Input()
    input.precipitation_rate = 1
    model.input = input

    model._Model__calculate_sediment_detachments("A-0")

    assert model.results.sediment_detachments["A-0"] == 6


def test_calculate_dispersion_coefficients():
    model = ModelTest()

    coeffs = dict(p_y=1, q_y=2, p_z=3, q_z=4)

    results = model._Model__calculate_dispersion_coefficients(coeffs, 2)

    assert results["y"] == 4
    assert results["z"] == 48

    results = model._Model__calculate_dispersion_coefficients(coeffs, 10001)

    assert results["z"] == 3 * math.pow(10001, 4)
    assert results["y"] == 1 * math.pow(1000, 1.5) * math.sqrt(10001)


def test_calculate_height_deposition_factors():
    model = ModelTest()

    input = Input()
    input.square_side = 2
    input.extreme_windspeeds = dict(A=1, B=1, C=1, D=1, E=1, F=1)
    input.distance = 1
    model.input = input

    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="A", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="B", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="C", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="D", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="E", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="F", p_z=1, q_z=1, p_y=1, q_y=1)
    )

    model.results.full_depletions.insert(
        "A-0", dict(A=1, B=1, C=1, D=1, E=1, F=1)
    )

    model._Model__calculate_height_deposition_factors("A-0")

    assert model.results.height_deposition_factors["A-0"] == pytest.approx(
        dict(A=0.199, B=0.199, C=0.199, D=0.199, E=0.199, F=0.199), 0.01
    )

    input.distance = 10001
    model.input = input

    model._Model__calculate_height_deposition_factors("A-0")

    assert model.results.height_deposition_factors["A-0"] == pytest.approx(
        dict(
            A=7.117e-5,
            B=7.117e-5,
            C=7.117e-5,
            D=7.117e-5,
            E=7.117e-5,
            F=7.117e-5,
        ),
        0.01,
    )


def test_caclculate_dilution_factors():
    model = ModelTest()

    input = Input()
    input.square_side = 2
    input.extreme_windspeeds = dict(A=1, B=1, C=1, D=1, E=1, F=1)
    input.distance = 1.01
    model.input = input

    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="A", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="B", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="C", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="D", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="E", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="F", p_z=1, q_z=1, p_y=1, q_y=1)
    )

    model.results.full_depletions.insert(
        "A-0", dict(A=1, B=1, C=1, D=1, E=1, F=1)
    )

    model._Model__caclculate_dilution_factors("A-0")

    assert model.results.dilution_factors["A-0"] == pytest.approx(
        dict(A=1.029, B=1.029, C=1.029, D=1.029, E=1.029, F=1.029), 0.01
    )

    input.distance = 10001
    model.input = input

    model._Model__caclculate_dilution_factors("A-0")

    assert model.results.dilution_factors["A-0"] == pytest.approx(
        dict(
            A=5.032e-8,
            B=5.032e-8,
            C=5.032e-8,
            D=5.032e-8,
            E=5.032e-8,
            F=5.032e-8,
        ),
        0.01,
    )


def test_calculate_rad_depletions():
    model = ModelTest()

    inp = Input()
    inp.distance = 1
    inp.extreme_windspeeds = dict(
        A=1, B=1 / 2, C=1 / 3, D=1 / 4, E=1 / 5, F=1 / 6
    )
    model.input = inp

    model.reference.db["nuclides"].insert(dict(name="A-0", decay_coeff=1))

    model._Model__calculate_rad_depletions("A-0")

    assert model.results.rad_depletions["A-0"] == pytest.approx(
        dict(
            A=math.exp(-1),
            B=math.exp(-2),
            C=math.exp(-3),
            D=math.exp(-4),
            E=math.exp(-5),
            F=math.exp(-6),
        ),
        0.01,
    )


def test_calculate_dry_depletions():
    model = ModelTest()

    inp = Input()
    inp.distance = 1
    inp.extreme_windspeeds = dict(A=1, B=1, C=1, D=1, E=1, F=1)
    model.input = inp

    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="A", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="B", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="C", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="D", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="E", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["diffusion_coefficients"].insert(
        dict(a_class="F", p_z=1, q_z=1, p_y=1, q_y=1)
    )
    model.reference.db["nuclides"].insert(dict(name="A-0", deposition_rate=1))

    model._Model__calculate_dry_depletions("A-0")

    assert model.results.dry_depletions["A-0"] == pytest.approx(
        dict(
            A=0.799861,
            B=0.799861,
            C=0.799861,
            D=0.799861,
            E=0.799861,
            F=0.799861,
        ),
        0.01,
    )


def test_calculate_wet_depletions():
    model = ModelTest()

    inp = Input()
    inp.distance = 1
    inp.extreme_windspeeds = dict(
        A=1, B=1 / 2, C=1 / 3, D=1 / 4, E=1 / 5, F=1 / 6
    )
    model.input = inp

    model.results.sediment_detachments.insert("A-0", 1)

    model._Model__calculate_wet_depletions("A-0")

    assert model.results.wet_depletions["A-0"] == pytest.approx(
        dict(
            A=math.exp(-1),
            B=math.exp(-2),
            C=math.exp(-3),
            D=math.exp(-4),
            E=math.exp(-5),
            F=math.exp(-6),
        ),
        0.01,
    )


def test_calculate_full_depletions():
    model = ModelTest()

    values = dict(A=1, B=2, C=3, D=4, E=5, F=6)
    model.results.rad_depletions.insert("A-0", values)
    model.results.dry_depletions.insert("A-0", values)
    model.results.wet_depletions.insert("A-0", values)

    model._Model__calculate_full_depletions("A-0")

    assert model.results.full_depletions["A-0"] == dict(
        A=math.pow(1, 3),
        B=math.pow(2, 3),
        C=math.pow(3, 3),
        D=math.pow(4, 3),
        E=math.pow(5, 3),
        F=math.pow(6, 3),
    )
