from ..database import Database


class _IReference:
    """Interface for reference data stored in database, handles all work
    related with its tables. The derivatives of that class should implement
    database attribute which is expected to have same API as
    :class:`dataset.Database`
    """

    def __init__(self):
        pass

    @property
    def db(self):
        """Pure virtual method of database access
        :raises NotImplementedError: always
        """
        raise NotImplementedError

    def all_nuclides(self):
        """List of all radionuclides in reference data
        :rtype: list
        """
        nuclides = list()
        for row in self.db["nuclides"]:
            nuclides.append(row["name"])
        return nuclides

    def radio_decay_coeff(self, nuclide):
        """Radioactivity decay coefficient, sec^-1
        :rtype: float
        """
        return float(self.__find_nuclide(nuclide)["decay_coeff"])

    def dose_rate_decay_coeff():
        """Dose rate decay coefficient due to all processes except
        radioactivity decay, sec^-1
        :rtype: float
        """
        return 1.27e-9

    def residence_time():
        """Population residence time in contaminated region for acute phase of
        a radiation accident, sec
        :rtype: float
        """
        return 3.15e7

    def nuclide_group(self, nuclide):
        """Nuclide group, e.g. aerosol, IRG etc.
        :rtype: str
        """
        return str(self.__find_nuclide(nuclide)["group"])

    def cloud_dose_coeff(self, nuclide):
        """Dose conversion factor for external exposure from radioactive cloud,
        (Sv*m^3)/(Bq*s)
        :rtype: float
        """
        return float(self.__find_nuclide(nuclide)["R_cloud"])

    def inhalation_dose_coeff(self, nuclide):
        """Dose conversion factor for nuclide intake with air, Sv/Bq
        :rtype: float
        """
        return float(self.__find_nuclide(nuclide)["R_inh"])

    def surface_dose_coeff(self, nuclide):
        """Dose conversion factor for external exposure from soil surface,
        (Sv*m^2)/(Bq*s)
        :rtype: float
        """
        return float(self.__find_nuclide(nuclide)["R_surface"])

    def respiration_rate(self, age):
        """Respiration rate, m^3/sec
        :rtype: float
        """
        rate = self.db["age_groups"].find_one(id=self.__get_age_group_id(age))[
            "respiration_rate"
        ]
        return float(rate)

    @property
    def tables(self):
        """Same as :property:`dataset.Database.tables`"""
        return self.db.tables

    def create_table(self, table_name, primary_id=None, primary_type=None):
        """Same as :method:`dataset.Database.create_table`"""
        return self.db.create_table(table_name, primary_id, primary_type)

    def load_table(self, table_name):
        """Same as :method:`dataset.Database.load_table`"""
        return self.db.load_table(table_name)

    def __find_nuclide(self, nuclide_name):
        return self.load_table("nuclides").find_one(name=nuclide_name)

    def __get_age_group_id(self, age):
        for age_group in self.db.load_table("age_groups"):
            if age >= age_group["lower_age"] and age < age_group["upper_age"]:
                return age_group["id"]
        raise ValueError(f"invalid provided age {age}")

    def __getitem__(self, key):
        return self.db[key]


class Reference(_IReference):
    """ORM class for reference data stored in file and represented with
    :class:`dataset.Database`
    """

    def __init__(self, dbname):
        super(Reference, self).__init__()
        self.__db = Database(dbname)

    @property
    def db(self):
        return self.__db
