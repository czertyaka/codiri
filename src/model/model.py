from .common import log, pasquill_gifford_classes
from .input import Input
from .results import Results
from .reference import Reference
import math
from scipy import integrate


class Model:
    """Doses & dilution factor calculator based on 2 scenario in Руководство
    по безопасности при использовании атомной энергии «Рекомендуемые методы
    оценки и прогнозирования радиационных последствий аварий на объектах
    ядерного топливного цикла (РБ-134-17)"""

    def __init__(self, reference_data_db_name):
        self.__results = Results()
        self.__reference = Reference(reference_data_db_name)
        self.input = Input()

    @property
    def input(self):
        return self.__input

    @input.setter
    def input(self, value):
        self.__input = value

    def reset(self):
        self.__results = Results()
        self.input = Input()

    def calculate(self):
        if self.__is_ready() is False:
            log("model instance is not ready for calculation")
            return

        for nuclide in self.input.activities:
            self.__calculate_concentration_integrals(nuclide)
            if self.reference.nuclide_group(nuclide) != "IRG":
                self.__calculate_height_concentration_integrals(nuclide)
                self.__calculate_depositions(nuclide)
                self.__calculate_e_inh(nuclide)
                self.__calculate_e_surface(nuclide)
            self.__calculate_e_cloud(nuclide)
            self.__calculate_e_total_10(nuclide)

        self.__calculate_e_max_10()

    @property
    def results(self):
        return self.__results

    @property
    def reference(self):
        return self.__reference

    def __is_ready(self):
        return (
            self.input.initialized()
            and self.input.consistent()
            and self.__is_input_valid()
        )

    def __is_input_valid(self):
        nuclides = self.reference.all_nuclides()
        for activity in self.input.activities:
            if activity["nuclide"] not in nuclides:
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
            self.reference.radio_decay_coeff(nuclide)
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

    def __calculate_height_concentration_integrals(self, nuclide):
        """РБ-134-17, p. 15, (2)"""

        activity = self.input.activities[nuclide]
        height_deposition_factor = self.results.height_deposition_factors[
            nuclide
        ]
        values = dict()

        for a_class in pasquill_gifford_classes:
            values[a_class] = activity * height_deposition_factor[a_class]

        self.results.height_concentration_integrals.insert(nuclide, values)

    def __calculate_concentration_integrals(self, nuclide):
        """РБ-134-17, p. 14, (1)"""

        activity = self.input.activities[nuclide]
        dilution_factors = self.results.dilution_factors[nuclide]
        values = dict()

        for a_class in pasquill_gifford_classes:
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

    def __calculate_height_deposition_factors(self, nuclide):
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

        self.results.height_concentration_integrals.insert(nuclide, values)

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
