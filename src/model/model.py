from .common import pasquill_gifford_classes, log, ValidatingMap
from .input import Input
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
    vertical_dispersion,
    sedimentation_factor,
    depletion_radiation,
    depletion_dry,
    depletion_wet,
    sediment_detachment_constant,
    depletion,
    dispersion_coeff_z,
    dispersion_coeff_y,
)
import math
import numpy as np
from ..activity import calculate_release_activity
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
        self._constraints = DefaultConstraints(reference.nuclides)

    def calculate(self, inp: Input) -> bool:
        """Execute calculations

        Args:
            inp (Input): input data

        Returns:
            bool: execution result
        """
        if not self.validate_input(inp):
            return False

        self._set_dispersion_coeffs()
        self._set_depletions(
            inp.extreme_windspeeds, inp.precipitation_rate, inp.terrain_type
        )
        self._set_sedimentation_factor(inp.extreme_windspeeds, inp.square_side)
        self._set_vertical_dispersion(inp.terrain_type)
        self._set_dilution_leval(
            inp.extreme_windspeeds, inp.square_side, inp.terrain_type
        )
        self._set_food_specific_activity_leval()
        self._set_deposition_leval(inp.distance)
        self._set_concentration_integral_levals(
            inp.specific_activities,
            inp.extreme_windspeeds,
            inp.blowout_time,
            inp.square_side,
        )
        self._set_xmax_leval(inp.nuclides, inp.buffer_area_radius)
        self._set_effective_doses_exposure_sources_levals(
            inp.age, inp.distance, inp.adults_annual_food_intake
        )
        self._set_effective_doses_total_levals()
        self._set_effective_doses_levals(inp.nuclides)

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

    def _set_dispersion_coeffs(self):
        """Set dispersion coefficients lazy evaluation"""
        self._sigma_z = LEval(
            lambda aclass, x: dispersion_coeff_z(
                self._reference.diffusion_coefficients(aclass)["p_z"],
                self._reference.diffusion_coefficients(aclass)["q_z"],
                x,
            )
        )
        self._sigma_y = LEval(
            lambda aclass, x: dispersion_coeff_y(
                self._reference.diffusion_coefficients(aclass)["p_y"],
                self._reference.diffusion_coefficients(aclass)["q_y"],
                x,
            )
        )

    def _set_depletions(
        self,
        wind_speeds: Dict[str, float],
        precipitation_rate: float,
        terrain_type: str,
    ):
        """Set depletion and depletion-related lazy evaluations

        Args:
            wind_speeds (Dict[str, float]): extreme wind speed per atmospheric
                class
            precipitation_rate (float): precipitation rate
            terrain_type (str): terrain type
        """
        self._depletion_rad = LEval(
            lambda aclass, nuclide, x: depletion_radiation(
                self._reference.nuclide_decay_coeff(nuclide),
                x,
                wind_speeds[aclass],
            )
        )
        self._depletion_dry = LEval(
            lambda aclass, nuclide, x: depletion_dry(
                self._reference.deposition_rate(nuclide),
                wind_speeds[aclass],
                lambda xx: self._sigma_z((aclass, xx)),
                self._reference.terrain_roughness(terrain_type),
                x,
            )
        )
        self._depletion_wet = LEval(
            lambda aclass, nuclide, x: depletion_wet(
                self._sediment_detachment_constant((nuclide)),
                x,
                wind_speeds[nuclide],
            )
        )
        self._sediment_detachment_constant = LEval(
            lambda nuclide: sediment_detachment_constant(
                self._reference.unitless_washing_capacity,
                precipitation_rate,
                self._reference.standard_washing_capacity(nuclide),
            )
        )
        self._depletion = LEval(
            lambda aclass, nuclide, x: depletion(
                self._depletion_rad((aclass, nuclide, x)),
                self._depletion_dry((aclass, nuclide, x)),
                self._depletion_wet((aclass, nuclide, x)),
            )
        )

    def _set_sedimentation_factor(
        self,
        wind_speeds: Dict[str, float],
        square_side: float,
    ):
        """Set sedimentation factor lazy evaluation

        Args:
            wind_speeds (Dict[str, float]): extreme wind speed per atmospheric
                class
            square_side (float): square source side length
        """
        self._sedimentation_factor = LEval(
            lambda aclass, nuclide, x: sedimentation_factor(
                self._depletion((aclass, nuclide, x)),
                wind_speeds[aclass],
                square_side / 2,
                lambda xx: self._sigma_y((nuclide, xx)),
                x,
            )
        )

    def _set_vertical_dispersion(self, terrain_type: str):
        """Set vertical dispersion factor lazy evaluation

        Args:
            terrain_type (str): terrain type
        """
        self._vert_dispersion = LEval(
            lambda aclass, x: vertical_dispersion(
                self._reference.mixing_layer_height,
                self._reference.terrain_roughness(terrain_type),
                self._sigma_z((aclass, x)),
                self._reference.terrain_roughness(terrain_type),
            )
        )

    def _set_dilution_leval(
        self,
        wind_speeds: Dict[str, float],
        square_side: float,
        terrain_type: str,
    ):
        """Set dilution lazy evaluation

        Args:
            wind_speeds (Dict[str, float]): extreme wind speed per atmospheric
                class
            square_side (float): square source side length
            terrain_type (str): terrain type
        """
        self._dilution = LEval(
            lambda aclass, nuclide, x: dilution_factor(
                self._depletion((aclass, nuclide, x)),
                lambda xx: self._sigma_y((aclass, xx)),
                lambda xx: self._sigma_z((aclass, xx)),
                wind_speeds[aclass],
                lambda xx, z: self._vert_dispersion((aclass, xx)),
                square_side / 2,
                x,
                self._reference.terrain_roughness(terrain_type),
            )
        )

    def _set_food_specific_activity_leval(self):
        """Set food specific activity lazy evaluation"""
        self._food_sa = LEval(
            lambda aclass, nuclide, x, food_id: food_specific_activity(
                self._reference.deposition_rate(nuclide),
                self._sediment_detachment_constant((nuclide)),
                self._ci((aclass, nuclide, x)),
                self._hdci((aclass, nuclide, x)),
                self._reference.atmosphere_accum_factor(nuclide, food_id),
                self._reference.soil_accum_factor(nuclide, food_id),
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
                self._sediment_detachment_constant((nuclide)),
                self._ci((aclass, nuclide, distance)),
                self._hdci((aclass, nuclide, distance)),
            )
        )

    def _set_concentration_integral_levals(
        self,
        specific_activities: ValidatingMap,
        wind_speeds: Dict[str, float],
        blowout_time: float,
        square_side: float,
    ):
        """Set concentration integrals lazy evaluations

        Args:
            specific_activities (ValidatingMap): specific activities dictionary
            wind_speeds (Dict[str, float]): extreme wind speed per atmospheric
                class
            blowout_time (float): blowout time
            square_side (float): square source side length
        """
        self._ci = LEval(
            lambda aclass, nuclide, x: concentration_integral(
                specific_activities[nuclide],
                calculate_release_activity(
                    specific_activities[nuclide],
                    wind_speeds[aclass],
                    blowout_time,
                    math.pow(square_side, 2),
                ),
                self._dilution((aclass, nuclide, x)),
            )
        )
        self._hdci = LEval(
            lambda aclass, nuclide, x: height_dist_concentration_integral(
                calculate_release_activity(
                    specific_activities[nuclide],
                    wind_speeds[aclass],
                    blowout_time,
                    math.pow(square_side, 2),
                ),
                self._sedimentation_factor((aclass, nuclide, x)),
            )
        )

    def _set_xmax_leval(
        self, nuclides: Tuple[str], buffer_area_distance: float
    ):
        """Set x_max lazy evaluation

        Args:
            nuclides (Tuple[str]): all the nuclides for current calculation
            buffer_area_distance (float): buffer area distance
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
                distances, make_dose_matrix(), buffer_area_distance
            )
        )

    def _set_effective_doses_exposure_sources_levals(
        self,
        age: int,
        distance: float,
        adults_annual_food_intake: Dict[str, float],
    ):
        """Set effective doses for all exposure sources lazy evaluations

        Args:
            age (int): population group age
            distance (float): distance
            adults_annual_food_intake (Dict[str, float]): adults annual food
                intake
        """
        self._annual_food_intake = LEval(
            lambda nuclide, food_id: annual_food_intake(
                self._reference.daily_metabolic_cost(
                    self._reference.food_critical_age_group(nuclide)
                ),
                self._reference.daily_metabolic_cost(
                    self._reference.age_group_id(100)
                ),
                adults_annual_food_intake(
                    self._reference.food_category(food_id)
                ),
            )
        )
        self._ed_food = LEval(
            lambda aclass, nuclide, x: effective_dose_food(
                self._reference.food_dose_coeff(nuclide),
                self._food_sa((aclass, nuclide, x)),
                {
                    food_id: self._food_sa((aclass, nuclide, x, food_id))
                    for food_id in self._reference.food_categories
                },
                {
                    food_id: self._annual_food_intake((nuclide, food_id))
                    for food_id in self._reference.food_categories
                },
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
                self._reference.residence_time,
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
                1,
                nuclide,
                self._ed_cloud((aclass, nuclide)),
                self._ed_inh((aclass, nuclide)),
                self._ed_surf((aclass, nuclide)),
                self._ed_food((aclass, nuclide, self._x_max())),
                {
                    nuclide: self._reference.nuclide_group(nuclide)
                    for nuclide in self._reference.nuclides
                },
            )
        )
        self._ed_total_acute = LEval(
            lambda aclass, nuclide: acute_total_effective_dose(
                nuclide,
                self._ed_cloud((aclass, nuclide)),
                self._ed_inh((aclass, nuclide)),
                self._ed_surf((aclass, nuclide)),
                {
                    nuclide: self._reference.nuclide_group(nuclide)
                    for nuclide in self._reference.nuclides
                },
            )
        )

    def _set_effective_doses_levals(self, nuclides: Tuple[str]):
        """Set effective doses lazy evaluations

        Args:
            nuclides (Tuple[str]): all the nuclides for current calculation
        """

        def make_ed_total_list(ed_total: LEval) -> Tuple[Dict[str, float]]:
            ed_total_results = list()
            for nuclide in nuclides:
                nuclide_ed_total = dict()
                for aclass in pasquill_gifford_classes:
                    nuclide_ed_total[aclass] = ed_total((aclass, nuclide))
                ed_total_results.append(nuclide_ed_total)
            return ed_total_results

        self._ed_acute = LEval(
            lambda: effective_dose(make_ed_total_list(self._ed_total_acute))
        )
        self._ed_for_period = LEval(
            lambda: effective_dose(make_ed_total_list(self._ed_total_period))
        )
