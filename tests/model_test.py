from codiri.src.model.model import Model
from codiri.src.model.results import Results
from codiri.src.model.reference import IReference
from codiri.src.database import InMemoryDatabase
from codiri.src.model.input import Input
import math


class ReferenceTest(IReference):
    def __init__(self):
        super(ReferenceTest, self).__init__()
        self.__db = InMemoryDatabase()

    @property
    def db(self):
        return self.__db

    @property
    def dose_rate_decay_coeff(self) -> float:
        return 0.5

    @property
    def residence_time(self) -> float:
        return -math.log(2)


class ModelTest(Model):
    def __init__(self):
        self._Model__results = Results()
        self.__reference = ReferenceTest()

    @property
    def reference(self):
        return self.__reference


def test_calculate_e_max_10():
    model = ModelTest()
    e_total_10_table = model.results.e_total_10
    e_total_10_table.insert("A-0", dict(A=0, B=6, C=2, D=8, E=4, F=10))
    e_total_10_table.insert("B-1", dict(A=1, B=7, C=3, D=9, E=5, F=11))

    model._Model__calculate_e_max_10()

    assert model.results.e_max_10 == 21


def test_calculate_e_total_10():
    model = ModelTest()

    e_cloud_table = model.results.e_cloud
    e_inh_table = model.results.e_inhalation
    e_surface_table = model.results.e_surface

    model.reference.db["nuclides"].insert(dict(name="A-0", group="aerosol"))
    e_cloud_table.insert("A-0", dict(A=0, B=6, C=2, D=8, E=4, F=10))
    e_inh_table.insert("A-0", dict(A=1, B=7, C=3, D=9, E=5, F=11))
    e_surface_table.insert("A-0", dict(A=2, B=8, C=4, D=10, E=6, F=12))

    model.reference.db["nuclides"].insert(dict(name="B-1", group="IRG"))
    e_cloud_table.insert("B-1", dict(A=0, B=6, C=2, D=8, E=4, F=10))
    e_inh_table.insert("B-1", dict(A=1, B=7, C=3, D=9, E=5, F=11))
    e_surface_table.insert("B-1", dict(A=2, B=8, C=4, D=10, E=6, F=12))

    model._Model__calculate_e_total_10("A-0")
    model._Model__calculate_e_total_10("B-1")

    e_total_10_table = model.results.e_total_10
    assert e_total_10_table["A-0"] == dict(A=3, B=21, C=9, D=27, E=15, F=33)
    assert e_total_10_table["B-1"] == dict(A=0, B=6, C=2, D=8, E=4, F=10)


def test_calculate_e_cloud():
    model = ModelTest()

    model.reference.db["nuclides"].insert(dict(name="A-0", R_cloud=1.5))
    model.results.concentration_integrals.insert(
        "A-0", dict(A=0, B=6, C=2, D=8, E=4, F=10)
    )

    model._Model__calculate_e_cloud("A-0")

    assert model.results.e_cloud["A-0"] == dict(A=0, B=9, C=3, D=12, E=6, F=15)


def test_calculate_e_inh():
    model = ModelTest()

    model.reference.db["nuclides"].insert(dict(name="A-0", R_inh=1.5))
    model.reference.db["age_groups"].insert(
        dict(id=0, lower_age=0, upper_age=10, respiration_rate=1)
    )
    model.reference.db["age_groups"].insert(
        dict(id=1, lower_age=10, upper_age=20, respiration_rate=2)
    )

    model.results.concentration_integrals.insert(
        "A-0", dict(A=0, B=6, C=2, D=8, E=4, F=10)
    )

    input = Input()
    input.age = 5
    model.input = input
    model._Model__calculate_e_inh("A-0")

    assert model.results.e_inhalation["A-0"] == dict(
        A=0, B=9, C=3, D=12, E=6, F=15
    )

    input.age = 15
    model.input = input
    model._Model__calculate_e_inh("A-0")

    assert model.results.e_inhalation["A-0"] == dict(
        A=0, B=18, C=6, D=24, E=12, F=30
    )


def test_calculate_residence_time_coeff():
    model = ModelTest()

    model.reference.db["nuclides"].insert(dict(name="A-0", decay_coeff=0.5))

    assert model._Model__calculate_residence_time_coeff("A-0") == -1
