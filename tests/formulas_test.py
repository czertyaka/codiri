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
)
import unittest


class TestFormulas(unittest.TestCase):
    def test_effective_dose(self):
        nuclide_aclass_doses = [
            {
                "A": 1,
                "B": 2,
                "C": 3,
                "D": 2,
                "E": 1,
                "F": 0,
            },
            {
                "A": 1,
                "B": 4,
                "C": 9,
                "D": 16,
                "E": 9,
                "F": 4,
            },
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
