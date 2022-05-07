from codiri.src.model.model import Model
from codiri.src.model.results import Results
from codiri.src.model.reference import _IReference
from codiri.src.database import InMemoryDatabase


class ReferenceTest(_IReference):
    def __init__(self):
        super(ReferenceTest, self).__init__()
        self.__db = InMemoryDatabase()

    @property
    def db(self):
        return self.__db


class ModelTest(Model):
    def __init__(self):
        self._Model__results = Results()
        self.__reference = ReferenceTest()

    @property
    def reference(self):
        return self.__reference


def test_calculate_e_max_10():
    model = ModelTest()
    e_total_10_table = model.results.create_e_total_10_table()
    e_total_10_table.insert(dict(nuclide="A-0", A=0, B=6, C=2, D=8, E=4, F=10))
    e_total_10_table.insert(dict(nuclide="B-1", A=1, B=7, C=3, D=9, E=5, F=11))
    model._Model__calculate_e_max_10()
    assert model.results["e_max_10"].count() == 1
    for value in model.results["e_max_10"]:
        assert value["e_max_10"] == 21


def test_calculate_e_total_10():
    model = ModelTest()
    e_total_10_table = model.results.create_e_total_10_table()
    e_cloud_table = model.results.create_e_cloud_table()
    e_inh_table = model.results.create_e_inh_table()
    e_surface_table = model.results.create_e_surface_table()

    model.reference["nuclides"].insert(dict(name="A-0", group="aerosol"))
    model.reference["nuclides"].insert(dict(name="B-1", group="IRG"))

    e_cloud_table.insert(dict(nuclide="A-0", A=0, B=6, C=2, D=8, E=4, F=10))
    e_cloud_table.insert(dict(nuclide="B-1", A=0, B=6, C=2, D=8, E=4, F=10))
    e_inh_table.insert(dict(nuclide="A-0", A=1, B=7, C=3, D=9, E=5, F=11))
    e_inh_table.insert(dict(nuclide="B-1", A=1, B=7, C=3, D=9, E=5, F=11))
    e_surface_table.insert(dict(nuclide="A-0", A=2, B=8, C=4, D=10, E=6, F=12))
    e_surface_table.insert(dict(nuclide="B-1", A=2, B=8, C=4, D=10, E=6, F=12))

    model._Model__calculate_e_total_10("A-0", "A")
    model._Model__calculate_e_total_10("A-0", "C")

    model._Model__calculate_e_total_10("B-1", "B")
    model._Model__calculate_e_total_10("B-1", "D")

    assert e_total_10_table.count() == 2

    assert e_total_10_table.find_one(nuclide="A-0")["A"] == 3
    assert e_total_10_table.find_one(nuclide="A-0")["C"] == 9

    assert e_total_10_table.find_one(nuclide="B-1")["B"] == 6
    assert e_total_10_table.find_one(nuclide="B-1")["D"] == 8
