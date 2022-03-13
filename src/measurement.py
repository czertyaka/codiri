class Measurement(object):
    """Holds info on activity measurement"""

    def __init__(self, activity, coo):
        """[specific activity] = Bq/kg"""
        self.__activity = activity
        coo.transform("EPSG:3857")
        self.__coo = coo

    @property
    def activity(self):
        return self.__activity

    @property
    def coo(self):
        return self.__coo
