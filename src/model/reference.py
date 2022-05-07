from ..database import Database


class _IReference:
    def __init__(self):
        pass

    @property
    def db(self):
        raise NotImplementedError

    @property
    def tables(self):
        return self.db.tables

    def create_table(self, table_name, primary_id=None, primary_type=None):
        return self.db.create_table(table_name, primary_id, primary_type)

    def load_table(self, table_name):
        return self.db.load_table(table_name)

    def find_nuclide(self, nuclide_name):
        return self.load_table("nuclides").find_one(name=nuclide_name)

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
