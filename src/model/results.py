from ..database import InMemoryDatabase
from .common import pasquill_gifford_classes


class NuclideVsAtmosphericClassTable:
    """Represents table containing certain value for each radionuclide and
    atmospheric stability class"""

    def __init__(self, database, table_name):
        """Create table instance
        :param database: database in which table will be created
        :type database: :class:`..database.IDatabase`
        :param table_name: table name
        :type table_name: str
        """
        self.__name = table_name
        self.__table = database.create_table(
            table_name,
            primary_id="nuclide",
            primary_type=database.types.string(7),
        )

        for a_class in pasquill_gifford_classes:
            self.__table.create_column(
                a_class, type=database.types.float, default=0
            )

    def __iter__(self):
        """Same as :method:`self.__table.__iter__()`"""
        return self.__table.__iter__()

    def __getitem__(self, nuclide) -> dict:
        """Get table row for nuclide"""
        row = dict(self.__table.find_one(nuclide=nuclide))
        row.pop("nuclide")
        return row

    def insert(self, nuclide, values):
        """Inserts values for certain nuclide
        :param nuclide: A nuclide for which values are provided
        :type nuclide: str
        :param values: Dictionary of values with Pasquill-Gifford classes as
            keys, e.g "A", "B", "C", "D", "E", "F"
        :type values: dict
        :raises ValueError: keys of `values` differs with expected
        """
        if sorted(values.keys()) != pasquill_gifford_classes:
            raise ValueError
        row = values
        row["nuclide"] = nuclide
        self.__table.upsert(row, ["nuclide"])

    @property
    def name(self) -> str:
        """Table name"""
        return self.__name


class Results:
    """Calculation results"""

    def __init__(self):
        db = InMemoryDatabase()
        self.__e_max_10 = 0
        self.__e_total_10 = NuclideVsAtmosphericClassTable(db, "e_total_10")
        self.__e_cloud = NuclideVsAtmosphericClassTable(db, "e_cloud")
        self.__e_inhalation = NuclideVsAtmosphericClassTable(db, "e_inh")
        self.__e_surface = NuclideVsAtmosphericClassTable(db, "e_surface")
        self.__concentration_integrals = NuclideVsAtmosphericClassTable(
            db, "concentration_integral"
        )
        self.__depositions = NuclideVsAtmosphericClassTable(db, "depositions")
        self.__e_total_10 = NuclideVsAtmosphericClassTable(db, "e_total_10")

    @property
    def e_max_10(self):
        return self.__e_max_10

    @e_max_10.setter
    def e_max_10(self, value):
        self.__e_max_10 = value

    @property
    def e_total_10(self):
        return self.__e_total_10

    @property
    def e_cloud(self):
        return self.__e_cloud

    @property
    def e_inhalation(self):
        return self.__e_inhalation

    @property
    def e_surface(self):
        return self.__e_surface

    @property
    def concentration_integrals(self):
        return self.__concentration_integrals

    @property
    def depositions(self):
        return self.__depositions
