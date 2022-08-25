from codiri.src.model.formulas import (
    effective_dose,
    acute_total_effective_dose,
    total_effective_dose_for_period,
    effective_dose_cloud,
    effective_dose_surface,
    residence_time_coeff,
    effective_dose_inhalation,
    effective_dose_food,
    annual_food_intake,
    food_max_distance,
    concentration_integral,
    height_dist_concentration_integral,
    deposition,
    food_specific_activity,
    dilution_factor,
    vertical_dispersion,
    sedimentation_factor,
)
from codiri.src.model.common import pasquill_gifford_classes
import numpy as np
import unittest


class TestSimpleFormulas(unittest.TestCase):
    def test_effective_dose(self):
        nuclide_aclass_doses = [
            {"A": 1, "B": 2, "C": 3, "D": 2, "E": 1, "F": 0},
            {"A": 1, "B": 4, "C": 9, "D": 16, "E": 9, "F": 4},
        ]
        self.assertEqual(effective_dose(nuclide_aclass_doses), 18)

    def test_acute_total_effective_dose(self):
        nuclide_groups = {"Cs-137": "aerosol", "Xe-133": "IRG"}
        cloud_ed = 1
        inh_ed = 2
        surf_ed = 3
        self.assertEqual(
            acute_total_effective_dose(
                "Xe-133", cloud_ed, inh_ed, surf_ed, nuclide_groups
            ),
            cloud_ed,
        )
        self.assertEqual(
            acute_total_effective_dose(
                "Cs-137", cloud_ed, inh_ed, surf_ed, nuclide_groups
            ),
            cloud_ed + inh_ed + surf_ed,
        )
        self.assertRaises(
            ValueError,
            lambda: acute_total_effective_dose(
                "unknown", cloud_ed, inh_ed, surf_ed, nuclide_groups
            ),
        )

    def test_total_effective_dose_for_period(self):
        nuclide_groups = {"Cs-137": "aerosol", "Xe-133": "IRG"}
        cloud_ed = 1
        inh_ed = 2
        surf_ed = 3
        food_ed = 4
        self.assertEqual(
            total_effective_dose_for_period(
                1, "Xe-133", cloud_ed, inh_ed, surf_ed, food_ed, nuclide_groups
            ),
            cloud_ed,
        )
        self.assertEqual(
            total_effective_dose_for_period(
                1, "Cs-137", cloud_ed, inh_ed, surf_ed, food_ed, nuclide_groups
            ),
            cloud_ed + inh_ed + surf_ed + food_ed,
        )
        self.assertRaises(
            ValueError,
            lambda: total_effective_dose_for_period(
                0, "Cs-137", cloud_ed, inh_ed, surf_ed, food_ed, nuclide_groups
            ),
        )
        self.assertRaises(
            ValueError,
            lambda: total_effective_dose_for_period(
                -1,
                "Cs-137",
                cloud_ed,
                inh_ed,
                surf_ed,
                food_ed,
                nuclide_groups,
            ),
        )
        self.assertRaises(
            NotImplementedError,
            lambda: total_effective_dose_for_period(
                2, "Cs-137", cloud_ed, inh_ed, surf_ed, food_ed, nuclide_groups
            ),
        )
        self.assertRaises(
            ValueError,
            lambda: total_effective_dose_for_period(
                1,
                "unknown",
                cloud_ed,
                inh_ed,
                surf_ed,
                food_ed,
                nuclide_groups,
            ),
        )

    def test_effective_dose_cloud(self):
        dc = 3
        ci = 7
        self.assertEqual(effective_dose_cloud(ci, dc), dc * ci)

    def test_effective_dose_surface(self):
        depo = 3
        dc = 7
        rtc = 2
        self.assertEqual(
            effective_dose_surface(depo, dc, rtc), depo * dc * rtc
        )

    def test_residence_time_coeff(self):
        dose_rate_decay_coeff = 1
        radioactive_decay_coeff = 2
        residence_time = 3
        self.assertAlmostEqual(
            residence_time_coeff(
                dose_rate_decay_coeff, radioactive_decay_coeff, residence_time
            ),
            0.333,
            3,
        )

    def test_effective_dose_inhalation(self):
        ci = 1
        dc = 2
        rr = 3
        self.assertEqual(effective_dose_inhalation(ci, dc, rr), ci * dc * rr)

    def test_effective_dose_food(self):
        dc = 1
        fi = {"milk": 2, "meat": 3}
        sa = {"meat": 4}
        with self.assertRaises(ValueError):
            effective_dose_food(dc, sa, fi)
        sa = {"milk": 5, "meat": 6}
        self.assertEqual(effective_dose_food(dc, sa, fi), 28)

    def test_annual_food_intake(self):
        dmc = 3
        dmc_adults = 4
        afi_adults = 1
        self.assertEqual(annual_food_intake(dmc, dmc_adults, afi_adults), 0.75)

    def test_concentration_integral(self):
        self.assertEqual(concentration_integral(3, 4), 12)
        self.assertEqual(concentration_integral(4, 3), 12)

    def test_height_dist_concentration_integral(self):
        self.assertEqual(height_dist_concentration_integral(3, 4), 12)
        self.assertEqual(height_dist_concentration_integral(4, 3), 12)

    def test_deposition(self):
        self.assertEqual(deposition(1, 2, 3, 4), 11)
        self.assertEqual(deposition(8, 7, 6, 5), 83)

    def test_food_specific_activity(self):
        self.assertEqual(food_specific_activity(1, 2, 3, 4, 5, 6), 89)
        self.assertEqual(food_specific_activity(6, 5, 4, 3, 2, 1), 93)

    def test_vertical_dispersion(self):
        self.assertAlmostEqual(vertical_dispersion(1, 2, 3, 4), 4.52753878, 8)
        self.assertAlmostEqual(vertical_dispersion(4, 3, 2, 1), 0.88831398, 8)


class TestFoodMaxDistanceFormula(unittest.TestCase):
    def test_invalid_first_band(self):
        distances = np.array((1, 2, 3))
        matrix = np.array([[[None]] for i in range(len(distances) - 1)])
        self.assertRaises(
            ValueError, lambda: food_max_distance(distances, matrix)
        )
        matrix = np.array([[[None]] for i in range(len(distances) + 1)])
        self.assertRaises(
            ValueError, lambda: food_max_distance(distances, matrix)
        )

    def test_invalid_second_band(self):
        distances = np.array((1, 2, 3))
        matrix = np.array(
            [
                [[None] for j in range(len(pasquill_gifford_classes) - 1)]
                for i in range(len(distances))
            ]
        )
        self.assertRaises(
            ValueError, lambda: food_max_distance(distances, matrix)
        )
        matrix = np.array(
            [
                [[None] for j in range(len(pasquill_gifford_classes) + 1)]
                for i in range(len(distances))
            ]
        )
        self.assertRaises(
            ValueError, lambda: food_max_distance(distances, matrix)
        )

    def test_single_max(self):
        distances = np.array((3, 4))
        matrix = np.array(
            [
                [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]],
                [[1, 2], [3, 4], [5, 6], [7, 8], [9, 50], [11, 12]],
            ]
        )
        self.assertEqual(food_max_distance(distances, matrix), 4)
        matrix = np.array(
            [
                [[1, 2], [3, 4], [1, 2], [3, 4], [1, 50], [3, 4]],
                [[10, 11], [12, 13], [14, 15], [16, 17], [18, 19], [20, 21]],
            ]
        )
        self.assertEqual(food_max_distance(distances, matrix), 3)

    def test_few_maxs(self):
        distances = np.array((5, 6, 7, 8))
        matrix = np.array(
            [
                [[3, 4], [5, 6], [3, 4], [5, 6], [3, 4], [5, 6]],
                [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]],
                [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]],
                [[1, 2], [3, 4], [1, 2], [3, 4], [1, 2], [3, 4]],
            ]
        )
        self.assertEqual(food_max_distance(distances, matrix), 7)

    def test_minimal_distance(self):
        distances = np.array((3, 4))
        matrix = np.array(
            [
                [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]],
                [[1, 2], [3, 4], [5, 6], [7, 8], [9, 50], [11, 12]],
            ]
        )
        self.assertEqual(food_max_distance(distances, matrix, 5), 5)


class TestDilutionFormula(unittest.TestCase):
    def test_wrong_args(self):
        with self.assertRaises(TypeError):
            dilution_factor(
                1, lambda: 2, lambda x: 3, 4, lambda z, x: 5, 6, 7, 8
            )
        with self.assertRaises(TypeError):
            dilution_factor(
                1, lambda x, y: 2, lambda x: 3, 4, lambda z, x: 5, 6, 7, 8
            )
        with self.assertRaises(TypeError):
            dilution_factor(
                1, lambda x: 2, lambda: 3, 4, lambda z, x: 5, 6, 7, 8
            )
        with self.assertRaises(TypeError):
            dilution_factor(
                1, lambda x: 2, lambda x, y: 3, 4, lambda z, x: 5, 6, 7, 8
            )
        with self.assertRaises(TypeError):
            dilution_factor(
                1, lambda x: 2, lambda x: 3, 4, lambda x: 5, 6, 7, 8
            )
        with self.assertRaises(TypeError):
            dilution_factor(
                1, lambda x: 2, lambda x: 3, 4, lambda z, x, y: 5, 6, 7, 8
            )

    def test_calculation(self):
        self.assertAlmostEqual(
            dilution_factor(
                1, lambda x: 2, lambda x: 3, 4, lambda z, x: 5, 6, 7, 8
            ),
            0.01381476,
            8,
        )
        self.assertAlmostEqual(
            dilution_factor(
                8, lambda x: 7, lambda x: 6, 5, lambda z, x: 4, 3, 2, 1
            ),
            0.02352978,
            8,
        )


class TestSedimentationFactor(unittest.TestCase):
    def test_wrong_args(self):
        with self.assertRaises(TypeError):
            sedimentation_factor(1, 2, 3, lambda: 4, 5)
        with self.assertRaises(TypeError):
            sedimentation_factor(1, 2, 3, lambda x, y: 4, 5)

    def test_calculation(self):
        self.assertAlmostEqual(
            sedimentation_factor(1, 2, 3, lambda x: 4, 5),
            0.02570567,
            8,
        )
        self.assertAlmostEqual(
            sedimentation_factor(5, 4, 3, lambda x: 2, 1),
            0.10183453,
            8,
        )
