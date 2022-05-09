import dataset


def _log(msg):
    print("db: " + msg)


class IDatabase:
    pass


class Database(dataset.Database, IDatabase):
    def __init__(self, dbname):
        super(Database, self).__init__(url=f"sqlite:///{dbname}")


class InMemoryDatabase(Database):
    def __init__(self):
        super(InMemoryDatabase, self).__init__(dbname=":memory:")
