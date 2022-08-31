from .common import pasquill_gifford_classes, log
from .input import Input
from .results import Results
from .reference import IReference
import math
from scipy import integrate
from ..activity import blowout_activity_flow


class Model:
    """Doses & dilution factor calculator based on 2 scenario in Руководство
    по безопасности при использовании атомной энергии «Рекомендуемые методы
    оценки и прогнозирования радиационных последствий аварий на объектах
    ядерного топливного цикла (РБ-134-17)"""

    def __init__(self, reference: IReference):
        self.__reference = reference
        self.__results = Results()
        self.input = Input()

    @property
    def input(self):
        return self.__input

    @input.setter
    def input(self, value):
        self.__input = value

    def calculate(self) -> bool:
        if self.__is_ready() is False:
            return False

        for nuclide in self.input.specific_activities:
            self.__calculate_sediment_detachments(nuclide)
            self.__calculate_depletions(nuclide)
            self.__caclculate_dilution_factors(nuclide)
            self.__calculate_height_deposition_factors(nuclide)
            self.__calculate_concentration_integrals(nuclide)
            if self.reference.nuclide_group(nuclide) != "IRG":
                self.__calculate_height_concentration_integrals(nuclide)
                self.__calculate_depositions(nuclide)
                self.__calculate_e_inh(nuclide)
                self.__calculate_e_surface(nuclide)
            self.__calculate_e_cloud(nuclide)
            self.__calculate_e_total_10(nuclide)

        self.__calculate_e_max_10()

        return True

    @property
    def results(self):
        return self.__results

    @property
    def reference(self) -> IReference:
        return self.__reference

    def __is_ready(self):
        return self.reference is not None and self.__is_input_ready()

    def __is_input_ready(self):
        if (
            self.input is None
            or not self.input.initialized()
            or self.input.distance > 5000
            or self.input.distance <= self.input.square_side / 2
        ):
            log(f"input is not ready '{self.input}'")
            return False
        for nuclide in self.input.specific_activities:
            if nuclide not in self.reference.nuclides():
                log(
                    f"unknown nuclide '{nuclide}'"
                    " (list of known nuclides "
                    f"'{self.reference.nuclides()}')"
                )
                return False
        return True

    def __calculate_e_max_10(self):
        """РБ-134-17, p. 3, (1)"""

        e_total_10_sums = list()

        for atmospheric_class in pasquill_gifford_classes:
            e_total_10_sum = 0
            for row in self.results.e_total_10:
                e_total_10_sum += row[atmospheric_class]
            e_total_10_sums.append(e_total_10_sum)

        self.results.e_max_10 = max(e_total_10_sums)

    def __calculate_e_total_10(self, nuclide):
        """РБ-134-17, p. 5, (3)"""

        e_total_10_dict = dict()
        nuclide_group = self.reference.nuclide_group(nuclide)

        for a_class in pasquill_gifford_classes:

            e_total_10 = 0
            e_total_10 += self.results.e_cloud[nuclide][a_class]

            if nuclide_group != "IRG":
                e_inh = self.results.e_inhalation[nuclide][a_class]
                e_surface = self.results.e_surface[nuclide][a_class]
                e_total_10 += e_inh + e_surface

            e_total_10_dict[a_class] = e_total_10

        self.results.e_total_10.insert(nuclide, e_total_10_dict)

    def __calculate_e_cloud(self, nuclide):
        """РБ-134-17, p. 7, (5)"""

        dose_coefficicent = self.reference.cloud_dose_coeff(nuclide)
        concentration_integrals = self.results.concentration_integrals[nuclide]
        values = dict()

        for a_class in pasquill_gifford_classes:
            values[a_class] = (
                dose_coefficicent * concentration_integrals[a_class]
            )

        self.results.e_cloud.insert(nuclide, values)

    def __calculate_e_inh(self, nuclide):
        """РБ-134-17, p. 9, (8)"""

        respiration_rate = self.reference.respiration_rate(self.input.age)
        concentration_integrals = self.results.concentration_integrals[nuclide]
        dose_coefficicent = self.reference.inhalation_dose_coeff(nuclide)
        values = dict()

        for a_class in pasquill_gifford_classes:
            values[a_class] = (
                respiration_rate
                * dose_coefficicent
                * concentration_integrals[a_class]
            )

        self.results.e_inhalation.insert(nuclide, values)

    def __calculate_e_surface(self, nuclide):
        """РБ-134-17, p. 8, (6)"""

        depositions = self.results.depositions[nuclide]
        dose_coefficicent = self.reference.surface_dose_coeff(nuclide)
        residence_time_coeff = self.__calculate_residence_time_coeff(nuclide)
        values = dict()

        for a_class in pasquill_gifford_classes:
            values[a_class] = (
                depositions[a_class] * dose_coefficicent * residence_time_coeff
            )

        self.results.e_surface.insert(nuclide, values)

    def __calculate_residence_time_coeff(self, nuclide):
        """РБ-134-17, p. 8, (7)"""

        decay_coeff_sum = (
            self.reference.nuclide_decay_coeff(nuclide)
            + self.reference.dose_rate_decay_coeff
        )

        return (
            1 - math.exp(-decay_coeff_sum * self.reference.residence_time)
        ) / decay_coeff_sum

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
            activity = self.__calculate_release(
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
            activity = self.__calculate_release(
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
                s_y = self.__calculate_dispersion_coefficients(
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
                    sigma_z = self.__calculate_dispersion_coefficients(
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
                disp_coeffs = self.__calculate_dispersion_coefficients(
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
        self.__calculate_rad_depletions(nuclide)
        self.__calculate_dry_depletions(nuclide)
        self.__calculate_wet_depletions(nuclide)
        self.__calculate_full_depletions(nuclide)

    def __calculate_rad_depletions(self, nuclide: str) -> None:
        """РБ-134-17, p. 28, (14)"""

        decay_coeff = self.reference.nuclide_decay_coeff(nuclide)
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
                sigma_z = self.__calculate_dispersion_coefficients(
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
