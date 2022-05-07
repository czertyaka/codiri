import dataset


def _log(msg):
    print("db: " + msg)


class Database(dataset.Database):
    def __init__(self, dbname):
        super(Database, self).__init__(url=f"sqlite:///{dbname}")


class InMemoryDatabase(Database):
    def __init__(self):
        super(InMemoryDatabase, self).__init__(dbname=":memory:")

    def drop_all(self):
        for table in self.tables:
            table.drop()


class ResultsDatabase(InMemoryDatabase):
    def __init__(self):
        super(ResultsDatabase, self).__init__()

    def create_e_total_10_table(self, atmospheric_classes):
        table = self.create_table(
            "e_total_10",
            primary_id="nuclide",
            primary_type=self.types.string(7),
        )
        for a_class in atmospheric_classes:
            table.create_column(a_class, self.types.float)
