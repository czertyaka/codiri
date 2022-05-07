from .results import ResultsDatabase
from ..database import Database


class Data:
    """Holds datasets required by model"""

    def __init__(self, dbname):
        self.__reference = Database(dbname)
        self.__results = ResultsDatabase()

    @property
    def reference(self):
        return self.__reference

    @property
    def results(self):
        return self.__results
