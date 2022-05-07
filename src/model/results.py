from ..database import InMemoryDatabase
from .common import pasquill_gifford_classes


class ResultsDatabase(InMemoryDatabase):
    """ORM class for model calculation results"""

    def __init__(self):
        super(ResultsDatabase, self).__init__()

    def create_e_total_10_table(self):
        table = self.create_table(
            "e_total_10",
            primary_id="nuclide",
            primary_type=self.types.string(7),
        )
        for a_class in pasquill_gifford_classes:
            table.create_column(a_class, self.types.float)
