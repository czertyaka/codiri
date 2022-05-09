from codiri.src.model.model import Model
from codiri.src.model.results import Results
from codiri.src.model.reference import _IReference
from codiri.src.database import InMemoryDatabase
from codiri.src.model.input import Input


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
    assert "e_total_10" not in model.results.tables

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

    assert "e_total_10" in model.results.tables

    e_total_10_table = model.results["e_total_10"]
    assert e_total_10_table.count() == 2

    assert e_total_10_table.find_one(nuclide="A-0")["A"] == 3
    assert e_total_10_table.find_one(nuclide="A-0")["C"] == 9

    assert e_total_10_table.find_one(nuclide="B-1")["B"] == 6
    assert e_total_10_table.find_one(nuclide="B-1")["D"] == 8


def test_calculate_e_cloud():
    model = ModelTest()
    assert "e_cloud" not in model.results.tables

    concentration_integrals_table = (
        model.results.create_concentration_integrals_table()
    )

    model.reference["nuclides"].insert(dict(name="A-0", R_cloud=1.5))
    concentration_integrals_table.insert(
        dict(nuclide="A-0", A=0, B=6, C=2, D=8, E=4, F=10)
    )

    model._Model__calculate_e_cloud("A-0", "A")
    model._Model__calculate_e_cloud("A-0", "B")
    model._Model__calculate_e_cloud("A-0", "C")
    model._Model__calculate_e_cloud("A-0", "D")
    model._Model__calculate_e_cloud("A-0", "E")
    model._Model__calculate_e_cloud("A-0", "F")

    assert "e_cloud" in model.results.tables

    e_cloud_table = model.results["e_cloud"]
    assert e_cloud_table.count() == 1
    row = e_cloud_table.find_one(nuclide="A-0")
    assert row["A"] == 0
    assert row["B"] == 9
    assert row["C"] == 3
    assert row["D"] == 12
    assert row["E"] == 6
    assert row["F"] == 15


def test_calculate_e_inh():
    model = ModelTest()
    assert "e_inh" not in model.results.tables

    model.results.create_concentration_integrals_table().insert(
        dict(nuclide="A-0", A=4)
    )

    model.reference["nuclides"].insert(dict(name="A-0", R_inh=1.5))

    model.reference["age_groups"].insert(
        dict(id=0, lower_age=0, upper_age=10, respiration_rate=1)
    )
    model.reference["age_groups"].insert(
        dict(id=1, lower_age=10, upper_age=20, respiration_rate=2)
    )

    input = Input()
    input.age = 5
    model.input = input
    model._Model__calculate_e_inh("A-0", "A")

    assert "e_inh" in model.results.tables

    e_inh_table = model.results["e_inh"]
    assert e_inh_table.count() == 1
    assert e_inh_table.find_one(nuclide="A-0")["A"] == 6

    input.age = 15
    model.input = input
    model._Model__calculate_e_inh("A-0", "A")

    assert e_inh_table.count() == 1
    assert e_inh_table.find_one(nuclide="A-0")["A"] == 12


def test_calculate_e_surface():
    model = ModelTest()
    assert "e_surface" not in model.results.tables

    model.results.create_deposition_table().insert(dict(nuclide="A-0", A=1))

    model.reference["nuclides"].insert(
        dict(name="A-0", R_surface=2, decay_coeff=3)
    )

    model._Model__calculate_e_surface("A-0", "A")

    assert "e_surface" in model.results.tables
