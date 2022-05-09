from ..database import Database


class _IReference:
    def __init__(self):
        pass

    @property
    def db(self):
        raise NotImplementedError

    def radio_decay_coeff(self, nuclide):
        """Radioactivity decay coefficient, sec^-1"""
        return self.find_nuclide(nuclide)["decay_coeff"]

    def dose_rate_decay_coeff():
        """Dose rate decay coefficient due to all processes except
        radioactivity decay, sec^-1"""
        return 1.27e-9

    def residence_time():
        """Population residence time in contaminated region for acute phase of
        a radiation accident, sec"""
        return 3.15e7

    @property
    def tables(self):
        return self.db.tables

    def create_table(self, table_name, primary_id=None, primary_type=None):
        return self.db.create_table(table_name, primary_id, primary_type)

    def load_table(self, table_name):
        return self.db.load_table(table_name)

    def find_nuclide(self, nuclide_name):
        return self.load_table("nuclides").find_one(name=nuclide_name)

    def get_age_group_id(self, age):
        for age_group in self.db.load_table("age_groups"):
            if age >= age_group["lower_age"] and age < age_group["upper_age"]:
                return age_group["id"]
        raise ValueError(f"invalid provided age {age}")

    def __getitem__(self, key):
        return self.db[key]


class Reference(_IReference):
    """ORM class for reference data"""

    def __init__(self, dbname):
        super(Reference, self).__init__()
        self.__db = Database(dbname)

    @property
    def db(self):
        return self.__db
