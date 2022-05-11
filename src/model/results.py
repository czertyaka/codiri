from ..database import InMemoryDatabase, IDatabase
from .common import pasquill_gifford_classes


class NuclideTable:
    """Represents table containing certain value with a row per nuclide"""

    def __init__(self, database: IDatabase, table_name: str):
        """Create table instance"""
        self.__name = table_name
        self.__table = database.create_table(
            table_name,
            primary_id="nuclide",
            primary_type=database.types.string(7),
        )
        self._create_columns(database)

    @property
    def name(self) -> str:
        """Table name"""
        return self.__name

    @property
    def table(self):
        """Table instance"""
        return self.__table

    def __iter__(self):
        """Same as :method:`self.__table.__iter__()`"""
        return self.__table.__iter__()

    def _create_columns(self, database: IDatabase) -> None:
        raise NotImplementedError


class NuclideVsAtmosphericClassTable(NuclideTable):
    """Represents table containing certain value for each radionuclide and
    atmospheric stability class"""

    def __init__(self, database: IDatabase, table_name: str):
        """Create table instance"""
        super(NuclideVsAtmosphericClassTable, self).__init__(
            database, table_name
        )

    def __getitem__(self, nuclide: str) -> dict:
        """Get table row for nuclide"""
        row = dict(self.table.find_one(nuclide=nuclide))
        row.pop("nuclide")
        return row

    def insert(self, nuclide: str, values: dict) -> None:
        """Inserts values for certain nuclide
        :param nuclide: A nuclide for which values are provided
        :type nuclide: str
        :param values: Dictionary of values with Pasquill-Gifford classes as
            keys, e.g "A", "B", "C", "D", "E", "F"
        :type values: dict
        :raises ValueError: keys of `values` differs with expected
        """
        if sorted(values.keys()) != sorted(pasquill_gifford_classes):
            raise ValueError
        row = values.copy()
        row["nuclide"] = nuclide
        self.table.upsert(row, ["nuclide"])

    def _create_columns(self, database: IDatabase) -> None:
        for a_class in pasquill_gifford_classes:
            self.table.create_column(
                a_class, type=database.types.float, default=0
            )


class NuclideOneColumnTable(NuclideTable):
    """Represents table containing single value for each radionuclide"""

    def __init__(self, database: IDatabase, table_name: str, column_name: str):
        self.__column_name = column_name
        super(NuclideOneColumnTable, self).__init__(database, table_name)

    def __getitem__(self, nuclide: str) -> float:
        """Get value for nuclide"""
        return self.table.find_one(nuclide=nuclide)[self.__column_name]

    def insert(self, nuclide: str, value: float) -> None:
        """Inserts value for certain nuclide"""
        row = {"nuclide": nuclide, self.__column_name: value}
        self.table.upsert(row, ["nuclide"])

    def _create_columns(self, database: IDatabase) -> None:
        self.table.create_column(
            self.__column_name, type=database.types.float, default=0
        )


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
        self.__sediment_detachments = NuclideOneColumnTable(
            db, "sediment_detachments", "sediment_detachment"
        )
        self.__height_concentration_integrals = NuclideVsAtmosphericClassTable(
            db, "height_concentration_integral"
        )
        self.__height_deposition_factors = NuclideVsAtmosphericClassTable(
            db, "height_deposition_factors"
        )
        self.__dilution_factors = NuclideVsAtmosphericClassTable(
            db, "dilution_factors"
        )
        self.__full_depletions = NuclideVsAtmosphericClassTable(
            db, "full_depletions"
        )
        self.__rad_depletions = NuclideVsAtmosphericClassTable(
            db, "rad_depletions"
        )
        self.__dry_depletions = NuclideVsAtmosphericClassTable(
            db, "dry_depletions"
        )
        self.__wet_depletions = NuclideVsAtmosphericClassTable(
            db, "wet_depletions"
        )

    @property
    def e_max_10(self) -> float:
        """Maximal effective dose at the acute accident period, Sv"""
        return self.__e_max_10

    @e_max_10.setter
    def e_max_10(self, value):
        self.__e_max_10 = value

    @property
    def e_total_10(self) -> NuclideVsAtmosphericClassTable:
        """Effective doses for each radionuclide and each atmospheric stability
        class, Sv
        """
        return self.__e_total_10

    @property
    def e_cloud(self) -> NuclideVsAtmosphericClassTable:
        """Effective doses due to external exposure from radioactive cloud for
        each radionuclide and each atmospheric stability class, Sv
        """
        return self.__e_cloud

    @property
    def e_inhalation(self) -> NuclideVsAtmosphericClassTable:
        """Effective doses due to nuclide intake with air for each radionuclide
        and each atmospheric stability class, Sv
        """
        return self.__e_inhalation

    @property
    def e_surface(self) -> NuclideVsAtmosphericClassTable:
        """Effective doses due to external exposure from soil surface for each
        radionuclide and each atmospheric stability class, Sv
        """
        return self.__e_surface

    @property
    def concentration_integrals(self) -> NuclideVsAtmosphericClassTable:
        """Concentration in surface air time integral for each radionuclide and
        each atmospheric stability class, Bq*seq/m^3
        """
        return self.__concentration_integrals

    @property
    def depositions(self) -> NuclideVsAtmosphericClassTable:
        """Summarized deposition value on ground surface due to dry and wet
        deposition, Bq/m^2"""
        return self.__depositions

    @property
    def sediment_detachments(self) -> NuclideOneColumnTable:
        """Radionuclide sediment detachment from soil values, sec^-1"""
        return self.__sediment_detachments

    @property
    def height_concentration_integrals(self) -> NuclideVsAtmosphericClassTable:
        """Height-phased concentration in surface air time integral for each
        radionuclide and each atmospheric stability class, Bq*seq/m^3
        """
        return self.__height_concentration_integrals

    @property
    def height_deposition_factors(self) -> NuclideVsAtmosphericClassTable:
        """Height-phased deposition factor for each radionuclide and each
        atmospheric stability class, sec/m^2
        """
        return self.__height_deposition_factors

    @property
    def dilution_factors(self) -> NuclideVsAtmosphericClassTable:
        """Dilution factor in surface air for each radionuclide and each
        atmospheric stability class, sec/m^3
        """
        return self.__dilution_factors

    @property
    def full_depletions(self) -> NuclideVsAtmosphericClassTable:
        """Full radioactive cloud depletion, unitless"""
        return self.__full_depletions

    @property
    def rad_depletions(self) -> NuclideVsAtmosphericClassTable:
        """Radioactive cloud depletion due to radioactive decay, unitless"""
        return self.__rad_depletions

    @property
    def dry_depletions(self) -> NuclideVsAtmosphericClassTable:
        """Radioactive cloud depletion due to dry deposition, unitless"""
        return self.__dry_depletions

    @property
    def wet_depletions(self) -> NuclideVsAtmosphericClassTable:
        """Radioactive cloud depletion due to wet deposition, unitless"""
        return self.__wet_depletions
