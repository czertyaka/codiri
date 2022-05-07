from .common import log, pasquill_gifford_classes
from .data import Data
from .input import Input


class Model:
    """Doses & dilution factor calculator based on 2 scenario in Руководство
    по безопасности при использовании атомной энергии «Рекомендуемые методы
    оценки и прогнозирования радиационных последствий аварий на объектах
    ядерного топливного цикла (РБ-134-17)"""

    def __init__(self, reference_data_db_name):
        self.__data = Data(reference_data_db_name)
        self.__input = Input()

    @property
    def input(self):
        return self.__input

    def reset(self):
        self.results.drop_all()
        self.__input = Input()

    def calculate(self):
        if self.__is_ready() is False:
            log("model instance is not ready for calculation")
            return

    @property
    def results(self):
        return self.__data.results

    def __is_ready(self):
        return self.input.initialized() and self.input.consistent()

    def __calculate_e_max_10(self):
        """РБ-134-17, p. 3, (1)"""

        e_total_10_sums = list()
        e_total_10_table = self.results.load_table("e_total_10")

        for atmospheric_class in pasquill_gifford_classes:
            e_total_10_sum = 0
            for nuclide in e_total_10_table:
                e_total_10_sum += nuclide[atmospheric_class]
            e_total_10_sums.append(e_total_10_sum)

        e_max_10 = max(e_total_10_sums)
        self.results["e_max_10"].insert(dict(e_max_10=e_max_10))