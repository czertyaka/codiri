from ..database import IDatabase, Database


class IReference:
    """Interface for reference data stored in database, handles all work
    related with its tables. The derivatives of that class should implement
    database attribute which is expected to have same API as
    :class:`.IDatabase`
    """

    def __init__(self):
        pass

    @property
    def db(self) -> IDatabase:
        """Pure virtual method of database access
        :raises NotImplementedError: always
        """
        raise NotImplementedError

    def all_nuclides(self) -> list:
        """List of all radionuclides in reference data"""
        nuclides = list()
        for row in self.db["nuclides"]:
            nuclides.append(row["name"])
        return nuclides

    def radio_decay_coeff(self, nuclide) -> float:
        """Radioactivity decay coefficient, sec^-1"""
        return float(self.__find_nuclide(nuclide)["decay_coeff"])

    def dose_rate_decay_coeff() -> float:
        """Dose rate decay coefficient due to all processes except
        radioactivity decay, sec^-1
        """
        return 1.27e-9

    def residence_time() -> float:
        """Population residence time in contaminated region for acute phase of
        a radiation accident, sec
        """
        return 3.15e7

    def nuclide_group(self, nuclide) -> str:
        """Nuclide group, e.g. aerosol, IRG etc."""
        return str(self.__find_nuclide(nuclide)["group"])

    def cloud_dose_coeff(self, nuclide) -> float:
        """Dose conversion factor for external exposure from radioactive cloud,
        (Sv*m^3)/(Bq*s)
        """
        return float(self.__find_nuclide(nuclide)["R_cloud"])

    def inhalation_dose_coeff(self, nuclide) -> float:
        """Dose conversion factor for nuclide intake with air, Sv/Bq"""
        return float(self.__find_nuclide(nuclide)["R_inh"])

    def surface_dose_coeff(self, nuclide) -> float:
        """Dose conversion factor for external exposure from soil surface,
        (Sv*m^2)/(Bq*s)
        """
        return float(self.__find_nuclide(nuclide)["R_surface"])

    def respiration_rate(self, age) -> float:
        """Respiration rate, m^3/sec"""
        rate = self.db["age_groups"].find_one(id=self.__get_age_group_id(age))[
            "respiration_rate"
        ]
        return float(rate)

    def __find_nuclide(self, nuclide_name):
        return self.db.load_table("nuclides").find_one(name=nuclide_name)

    def __get_age_group_id(self, age):
        for age_group in self.db.load_table("age_groups"):
            if age >= age_group["lower_age"] and age < age_group["upper_age"]:
                return age_group["id"]
        raise ValueError(f"invalid provided age {age}")

    def __getitem__(self, key):
        return self.db[key]


class Reference(IReference):
    """ORM class for reference data stored in file and represented with
    :class:`dataset.Database`
    """

    def __init__(self, dbname):
        super(Reference, self).__init__()
        self.__db = Database(dbname)

    @property
    def db(self) -> Database:
        return self.__db
