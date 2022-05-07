from ..database import Database


class Reference(Database):
    """ORM class for reference data"""

    def __init__(self, dbname):
        super(Reference, self).__init__(dbname)

    def find_nuclide(self, nuclide_name):
        return self.load_table("nuclides").find_one(name=nuclide_name)
