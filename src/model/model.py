from .common import pasquill_gifford_classes, log
from .input import Input
from .results import Results
from .reference import IReference
from .constraints import IConstraints, ConstraintsComplianceError
from .lazy_eval import LazyEvaluation as LEval
from .formulas import (
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
)
import math
import numpy as np
from scipy import integrate
from ..activity import blowout_activity_flow
from typing import Tuple, Dict


class DefaultConstraints(IConstraints):

    """Default input constraints class"""

    def __init__(self, known_nuclides: Tuple[str]):
        """DefaultConstraints constructor

        Args:
            known_nuclides (Tuple[str]): known nuclides
        """
        super(DefaultConstraints, self).__init__()
        self.add(
            lambda inp: inp.distance <= 50000,
            lambda inp: f"the distance '{inp.distance} m' exceeds the maximum "
            "allowed '50000 m'",
        )
        self.add(
            lambda inp: inp.distance > (inp.square_side / 2),
            lambda inp: f"the distance '{inp.distance} m' should exceed the "
            f"half of the square side '{(inp.square_side / 2)} m'",
        )

        def known_nuclides_validator(inp: Input) -> bool:
            for nuclide in inp.specific_activities:
                if nuclide not in known_nuclides:
                    return False
            return True

        self.add(
            known_nuclides_validator,
            lambda inp: "found specific activity with unknown nuclide",
        )


class Model:
    """Doses & dilution factor calculator based on 2 scenario in Руководство
    по безопасности при использовании атомной энергии «Рекомендуемые методы
    оценки и прогнозирования радиационных последствий аварий на объектах
    ядерного топливного цикла (РБ-134-17)"""

    def __init__(self, reference: IReference):
        """Model constructor

        Args:
            reference (IReference): Reference data class interface

        Raises:
            ValueError: invalid reference instance
        """
        if reference is None:
            raise ValueError("invalid reference instance")
        self._reference = reference
        self._constraints = DefaultConstraints(reference.all_nuclides())
        self._results = Results()

    def calculate(self, inp: Input) -> bool:
        """Execute calculations

        Args:
            inp (Input): input data

        Returns:
            bool: execution result
        """
        if not self.validate_input(inp):
            return False

        self._set_xmax_leval(inp.specific_activities.keys())
        self._set_effective_doses_exposure_sources_levals(inp.age)
        self._set_effective_doses_total_levals()
        self._set_effective_doses_levals(inp.specific_activities.keys())

        self._ed_acute.exec()

        return True

    def validate_input(self, inp: Input) -> bool:
        """Validate input

        Args:
            inp (Input): input

        Returns:
            bool: validation result
        """
        if inp is not None and inp.initialized():
            try:
                self._constraints.validate(inp)
                return True
            except ConstraintsComplianceError as err:
                log(f"input failed to comply constraints: {err}")
        log(f"invalid input: {inp}")
        return False

    def _set_xmax_leval(self, nuclides: Tuple[str]):
        """Set x_max lazy evaluation

        Args:
            nuclides (Tuple[str]): all the nuclides for current calculation
        """
        distances_count = 100
        distances = np.array(
            [
                math.pow(math.sqrt(50000) / (distances_count - 1) * i, 2)
                for i in range(distances_count)
            ]
        )

        def make_dose_matrix():
            return np.array(
                [
                    [
                        [
                            self._ed_food.exec(aclass, nuclide, x)
                            for nuclide in nuclides
                        ]
                        for aclass in pasquill_gifford_classes
                    ]
                    for x in distances
                ]
            )

        self._x_max = LEval(
            lambda: food_max_distance(
                distances,
                make_dose_matrix(),
                0,  # TODO: add minimal distance
            )
        )

    def _set_effective_doses_exposure_sources_levals(self, age: int):
        """Set effective doses for all exposure sources lazy evaluations

        Args:
            age (int): population group age
        """
        self._annual_food_intake = LEval(
            lambda: annual_food_intake(
                1,  # TODO: daily metabolic cost
                1,  # TODO: adults daily metabolic cost
                1,  # TODO: adults annual food intake
            )
        )
        self._ed_food = LEval(
            lambda aclass, nuclide, x: effective_dose_food(
                1,  # TODO: food dose conversion coeff
                dict(),  # TODO: food specific activity
                self._annual_food_intake.exec(),
            )
        )
        self._ed_inh = LEval(
            lambda aclass, nuclide: effective_dose_inhalation(
                1,  # TODO: concentration integral
                self._reference.inhalation_dose_coeff(nuclide),
                self._reference.respiration_rate(age),
            )
        )
        self._residence_time_coeff = LEval(
            lambda nuclide: residence_time_coeff(
                self._reference.dose_rate_decay_coeff,
                self._reference.radio_decay_coeff(nuclide),
                self._reference.residence_time(0),  # TODO
            )
        )
        self._ed_surf = LEval(
            lambda aclass, nuclide: effective_dose_surface(
                1,  # TODO: concentration integral
                self._reference.surface_dose_coeff(nuclide),
                self._residence_time_coeff.exec((nuclide,)),
            )
        )
        self._ed_cloud = LEval(
            lambda aclass, nuclide: effective_dose_cloud(
                1,  # TODO: concentration integral
                self._reference.cloud_dose_coeff(nuclide),
            )
        )

    def _set_effective_doses_total_levals(self):
        """Set total effective doses for acute phase and a period lazy
        evaluations
        """
        self._ed_total_period = LEval(
            lambda aclass, nuclide: total_effective_dose_for_period(
                1,  # TODO: take from input
                nuclide,
                self._ed_cloud.exec((aclass, nuclide)),
                self._ed_inh.exec((aclass, nuclide)),
                self._ed_surf.exec((aclass, nuclide)),
                self._ed_food.exec((aclass, nuclide, self._x_max.exec())),
                1,  # TODO: nuclide groups
            )
        )
        self._ed_total_acute = LEval(
            lambda aclass, nuclide: acute_total_effective_dose(
                nuclide,
                self._ed_cloud.exec((aclass, nuclide)),
                self._ed_inh.exec((aclass, nuclide)),
                self._ed_surf.exec((aclass, nuclide)),
                1,  # TODO: nuclide groups
            )
        )

    def _set_effective_doses_levals(self, nuclides: Tuple[str]):
        """Set effective doses lazy evaluations

        Args:
            nuclides (Tuple[str]): all the nuclides for current calculation
        """

        def make_ed_total_list(ed_total: LEval) -> Tuple[Dict[str, float]]:
            ed_total = list()
            for nuclide in nuclides:
                nuclide_ed_total = dict()
                for aclass in pasquill_gifford_classes:
                    nuclide_ed_total[aclass] = ed_total.exec((aclass, nuclide))
                ed_total.append(nuclide_ed_total)
            return ed_total

        self._ed_acute = LEval(
            lambda: effective_dose(make_ed_total_list(self._ed_total_acute))
        )
        self._ed_for_period = LEval(
            lambda: effective_dose(make_ed_total_list(self._ed_total_period))
        )

    def __calculate_depositions(self, nuclide):
        """РБ-134-17, p. 17, (5)"""

        depositon_rate = self.reference.deposition_rate(nuclide)
        sediment_detachment = self.results.sediment_detachments[nuclide]
        concentration_integrals = self.results.concentration_integrals[nuclide]
        height_concentration_integrals = (
            self.results.height_concentration_integrals[nuclide]
        )
        values = dict()

        for a_class in pasquill_gifford_classes:
            values[a_class] = (
                depositon_rate * concentration_integrals[a_class]
                + sediment_detachment * height_concentration_integrals[a_class]
            )

        self.results.depositions.insert(nuclide, values)

    def __calculate_release(
        self, specific_activity: float, windspeed: float
    ) -> float:
        return (
            blowout_activity_flow(specific_activity, windspeed)
            * self.input.blowout_time
            * math.pow(self.input.square_side, 2)
        )

    def __calculate_height_concentration_integrals(self, nuclide):
        """РБ-134-17, p. 15, (2)"""

        height_deposition_factor = self.results.height_deposition_factors[
            nuclide
        ]
        windspeeds = self.input.extreme_windspeeds
        specific_activity = self.input.specific_activities[nuclide]
        values = dict()

        for a_class in pasquill_gifford_classes:
            activity = self._calculate_release(
                specific_activity, windspeeds[a_class]
            )
            values[a_class] = activity * height_deposition_factor[a_class]

        self.results.height_concentration_integrals.insert(nuclide, values)

    def __calculate_concentration_integrals(self, nuclide):
        """РБ-134-17, p. 14, (1)"""

        dilution_factors = self.results.dilution_factors[nuclide]
        windspeeds = self.input.extreme_windspeeds
        specific_activity = self.input.specific_activities[nuclide]
        values = dict()

        for a_class in pasquill_gifford_classes:
            activity = self._calculate_release(
                specific_activity, windspeeds[a_class]
            )
            values[a_class] = activity * dilution_factors[a_class]

        self.results.concentration_integrals.insert(nuclide, values)

    def __calculate_sediment_detachments(self, nuclide):
        """РБ-134-17, p. 29, (17)"""

        precipitation_rate = self.input.precipitation_rate
        standard_washing_capacity = self.reference.standard_washing_capacity(
            nuclide
        )
        unitless_washing_capacity = self.reference.unitless_washing_capacity

        value = (
            precipitation_rate
            * standard_washing_capacity
            * unitless_washing_capacity
        )

        self.results.sediment_detachments.insert(nuclide, value)

    def __calculate_height_deposition_factors(self, nuclide: str):
        """РБ-134-17, p. 28, (13)"""

        windspeeds = self.input.extreme_windspeeds
        side_half = self.input.square_side / 2
        depletions = self.results.full_depletions[nuclide]
        values = dict()

        for a_class in pasquill_gifford_classes:
            factor = depletions[a_class] / (
                math.sqrt(math.pi)
                * windspeeds[a_class]
                * 4
                * math.pow(side_half, 2)
            )

            diffusion_coefficients = self.reference.diffusion_coefficients(
                a_class
            )

            def subintegral_func(x):
                s_y = self._calculate_dispersion_coefficients(
                    diffusion_coefficients, self.input.distance - x
                )["y"]
                return math.erf(side_half / (math.sqrt(2) * s_y))

            values[a_class] = (
                factor
                * integrate.quad(subintegral_func, -side_half, side_half)[0]
            )

        self.results.height_deposition_factors.insert(nuclide, values)

    def __calculate_dispersion_coefficients(
        self, diffusion_coefficients: dict, x: float
    ) -> dict:
        """РБ-134-17, p. 29, (19) (20)"""

        p_z = diffusion_coefficients["p_z"]
        q_z = diffusion_coefficients["q_z"]
        p_y = diffusion_coefficients["p_y"]
        q_y = diffusion_coefficients["q_y"]

        z = p_z * math.pow(x, q_z)
        y = (
            p_y * math.pow(x, q_y)
            if x < 10000
            else p_y * math.pow(1000, q_y - 0.5) * math.sqrt(x)
        )

        return dict(z=z, y=y)

    def __caclculate_dilution_factors(self, nuclide: str) -> None:
        """РБ-134-17, p. 27, (11)"""

        windspeeds = self.input.extreme_windspeeds
        side_half = self.input.square_side / 2
        depletions = self.results.full_depletions[nuclide]
        z = self.reference.terrain_clearance
        h_mix = self.reference.mixing_layer_height
        h_rel = self.reference.terrain_roughness(self.input.terrain_type)
        values = dict()

        for a_class in pasquill_gifford_classes:
            factor = depletions[a_class] / (
                math.sqrt(2 * math.pi)
                * windspeeds[a_class]
                * 4
                * math.pow(side_half, 2)
            )

            diffusion_coefficients = self.reference.diffusion_coefficients(
                a_class
            )

            def vertical_dispersion_factor(x: float) -> float:
                """РБ-134-17, p. 27, (12)"""

                value = 0
                for n in range(-2, 3):
                    sigma_z = self._calculate_dispersion_coefficients(
                        diffusion_coefficients, x
                    )["z"]
                    consequent = 2 * math.pow(sigma_z, 2)
                    exp1 = (
                        -math.pow((2 * n * h_mix + h_rel - z), 2) / consequent
                    )
                    exp2 = (
                        -math.pow((2 * n * h_mix - h_rel - z), 2) / consequent
                    )
                    value += math.exp(exp1) + math.exp(exp2)

                return value

            def subintegral_func(x):
                diff = self.input.distance - x
                vert_disp = vertical_dispersion_factor(diff)
                disp_coeffs = self._calculate_dispersion_coefficients(
                    diffusion_coefficients, diff
                )
                erf = math.erf(side_half / (math.sqrt(2) * disp_coeffs["y"]))
                return vert_disp * erf / disp_coeffs["z"]

            values[a_class] = (
                factor
                * integrate.quad(subintegral_func, -side_half, side_half)[0]
            )

        self.results.dilution_factors.insert(nuclide, values)

    def __calculate_depletions(self, nuclide: str) -> None:
        self._calculate_rad_depletions(nuclide)
        self._calculate_dry_depletions(nuclide)
        self._calculate_wet_depletions(nuclide)
        self._calculate_full_depletions(nuclide)

    def __calculate_rad_depletions(self, nuclide: str) -> None:
        """РБ-134-17, p. 28, (14)"""

        decay_coeff = self.reference.radio_decay_coeff(nuclide)
        windspeeds = self.input.extreme_windspeeds
        dist = self.input.distance
        values = dict()

        for a_class in pasquill_gifford_classes:
            values[a_class] = math.exp(
                -decay_coeff * dist / windspeeds[a_class]
            )

        self.results.rad_depletions.insert(nuclide, values)

    def __calculate_dry_depletions(self, nuclide: str) -> None:
        """РБ-134-17, p. 28, (15)"""

        windspeeds = self.input.extreme_windspeeds
        depositon_rate = self.reference.deposition_rate(nuclide)
        h_rel = self.reference.terrain_roughness(self.input.terrain_type)
        dist = self.input.distance
        values = dict()

        for a_class in pasquill_gifford_classes:
            factor = (
                math.sqrt(2 / math.pi) * depositon_rate / windspeeds[a_class]
            )
            diffusion_coefficients = self.reference.diffusion_coefficients(
                a_class
            )

            def subintegral_func(x: float) -> float:
                sigma_z = self._calculate_dispersion_coefficients(
                    diffusion_coefficients, x
                )["z"]
                exp_factor = -math.pow((h_rel / sigma_z), 2) / 2
                return math.exp(exp_factor) / sigma_z

            integral = integrate.quad(subintegral_func, 0, dist)[0]
            values[a_class] = math.exp(-factor * integral)

        self.results.dry_depletions.insert(nuclide, values)

    def __calculate_wet_depletions(self, nuclide: str) -> None:
        """РБ-134-17, p. 28, (16)"""

        windspeeds = self.input.extreme_windspeeds
        dist = self.input.distance
        detachment = self.results.sediment_detachments[nuclide]
        values = dict()

        for a_class in pasquill_gifford_classes:
            values[a_class] = math.exp(
                -detachment * dist / windspeeds[a_class]
            )

        self.results.wet_depletions.insert(nuclide, values)

    def __calculate_full_depletions(self, nuclide: str) -> None:
        """РБ-134-17, p. 29, (18)"""

        rad = self.results.rad_depletions[nuclide]
        dry = self.results.dry_depletions[nuclide]
        wet = self.results.wet_depletions[nuclide]
        values = dict()

        for a_class in pasquill_gifford_classes:
            values[a_class] = rad[a_class] * dry[a_class] * wet[a_class]

        self.results.full_depletions.insert(nuclide, values)
