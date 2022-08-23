from .common import pasquill_gifford_classes, log, ValidatingMap
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
    concentration_integral,
    height_dist_concentration_integral,
    deposition,
    food_specific_activity,
    dilution_factor,
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

        self._set_dilution_leval(
            inp.extreme_windspeeds, inp.square_side, inp.terrain_roughness
        )
        self._set_food_specific_activity_leval()
        self._set_deposition_leval()
        self._set_concentration_integral_levals(inp.specific_activities)
        self._set_xmax_leval(inp.specific_activities.keys())
        self._set_effective_doses_exposure_sources_levals(inp.age)
        self._set_effective_doses_total_levals()
        self._set_effective_doses_levals(inp.specific_activities.keys())

        self._ed_acute()

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

    def _set_dilution_leval(
        self,
        wind_speeds: Dict[str, float],
        square_side: float,
        terrain_clearance: float,
    ):
        """Set dilution lazy evaluation

        Args:
            wind_speeds (Dict[str, float]): extreme wind speed per atmospheric
                class
            square_side (float): square source side length
            terrain_clearance (float): terrain clearance
        """
        self._dilution = LEval(
            lambda aclass, nuclide, x: dilution_factor(
                1,  # TODO: add depletion
                lambda x: 2,  # TODO: add sigma_y
                lambda x: 3,  # TODO: add sigma_z
                wind_speeds[aclass],
                lambda z, x: 5,  # TODO: add G(z, xi - x)
                square_side / 2,
                x,
                terrain_clearance,
            )
        )

    def _set_food_specific_activity_leval(self):
        """Set food specific activity lazy evaluation"""
        self._food_sa = LEval(
            lambda aclass, nuclide, x: food_specific_activity(
                self._reference.deposition_rate(nuclide),
                2,  # TODO: add sediment detachment constant
                self._ci((aclass, nuclide, x)),
                self._hdci((aclass, nuclide, x)),
                5,  # TODO: add atmosphere accumulation factor
                6,  # TODO: add soil accumulation factor
            )
        )

    def _set_deposition_leval(self, distance: float):
        """Set deposition lazy evaluation

        Args:
            distance (float): distance
        """
        self._deposition = LEval(
            lambda aclass, nuclide: deposition(
                self._reference.deposition_rate(nuclide),
                2,  # TODO: add sediment detachment constant
                self._ci((aclass, nuclide, distance)),
                self._hdci((aclass, nuclide, distance)),
            )
        )

    def _set_concentration_integral_levals(
        self, specific_activities: ValidatingMap
    ):
        """Set concentration integrals lazy evaluations

        Args:
            specific_activities (ValidatingMap): specific activities dictionary
        """
        self._ci = LEval(
            lambda aclass, nuclide, x: concentration_integral(
                specific_activities[nuclide],
                2,  # TODO: add dilution factor
            )
        )
        self._hdci = LEval(
            lambda aclass, nuclide, x: height_dist_concentration_integral(
                specific_activities[nuclide],
                2,  # TODO: add sedimentation factor
            )
        )

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
                            self._ed_food(aclass, nuclide, x)
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

    def _set_effective_doses_exposure_sources_levals(
        self, age: int, distance: float
    ):
        """Set effective doses for all exposure sources lazy evaluations

        Args:
            age (int): population group age
            distance (float): distance
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
                self._food_sa((aclass, nuclide, x)),
                self._annual_food_intake(),
            )
        )
        self._ed_inh = LEval(
            lambda aclass, nuclide: effective_dose_inhalation(
                self._ci((aclass, nuclide, distance)),
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
                self._deposition((aclass, nuclide)),
                self._reference.surface_dose_coeff(nuclide),
                self._residence_time_coeff((nuclide,)),
            )
        )
        self._ed_cloud = LEval(
            lambda aclass, nuclide: effective_dose_cloud(
                self._ci((aclass, nuclide, distance)),
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
                self._ed_cloud((aclass, nuclide)),
                self._ed_inh((aclass, nuclide)),
                self._ed_surf((aclass, nuclide)),
                self._ed_food((aclass, nuclide, self._x_max())),
                1,  # TODO: nuclide groups
            )
        )
        self._ed_total_acute = LEval(
            lambda aclass, nuclide: acute_total_effective_dose(
                nuclide,
                self._ed_cloud((aclass, nuclide)),
                self._ed_inh((aclass, nuclide)),
                self._ed_surf((aclass, nuclide)),
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
                    nuclide_ed_total[aclass] = ed_total((aclass, nuclide))
                ed_total.append(nuclide_ed_total)
            return ed_total

        self._ed_acute = LEval(
            lambda: effective_dose(make_ed_total_list(self._ed_total_acute))
        )
        self._ed_for_period = LEval(
            lambda: effective_dose(make_ed_total_list(self._ed_total_period))
        )

    # TODO: consider!!!
    def __calculate_release(
        self, specific_activity: float, windspeed: float
    ) -> float:
        return (
            blowout_activity_flow(specific_activity, windspeed)
            * self.input.blowout_time
            * math.pow(self.input.square_side, 2)
        )

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
