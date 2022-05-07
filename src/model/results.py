from ..database import InMemoryDatabase
from .common import pasquill_gifford_classes


class ResultsDatabase(InMemoryDatabase):
    """ORM class for model calculation results"""

    def __init__(self):
        super(ResultsDatabase, self).__init__()

    def create_e_total_10_table(self):
        self.__create_nuclide_vs_atmospheric_class_empty_table("e_total_10")

    def __create_nuclide_vs_atmospheric_class_empty_table(self, name):
        table = self.create_table(
            name,
            primary_id="nuclide",
            primary_type=self.types.string(7),
        )
        for a_class in pasquill_gifford_classes:
            table.create_column(a_class, self.types.float)
