from codiri.src.model.model import Model
from codiri.src.model.results import ResultsDatabase


class ModelTest(Model):
    def __init__(self):
        super(ModelTest, self).__init__(
            reference_data_db_name="../data/reference_data.db"
        )
        self.__results = ResultsDatabase()

    @property
    def results(self):
        return self.__results


def test_calculate_e_max_10():
    model = ModelTest()
    model.results.create_e_total_10_table()
    e_total_10_table = model.results["e_total_10"]
    e_total_10_table.insert(dict(nuclide="A-0", A=0, B=6, C=2, D=8, E=4, F=10))
    e_total_10_table.insert(dict(nuclide="B-1", A=1, B=7, C=3, D=9, E=5, F=11))
    model._Model__calculate_e_max_10()
    assert model.results["e_max_10"].count() == 1
    for value in model.results["e_max_10"]:
        assert value["e_max_10"] == 21
