class SoilActivity(object):
    """Holds info on specific and surface activity of contaminated soil"""

    def __init__(self, specific_activity, soil_density=1.4):
        """[specific_activity] = Bq/kg; [soil_density] = gm/cm^3"""
        self.__specific = specific_activity
        self.__calculate_surface_activity(soil_density)

    def __calculate_surface_activity(self, soil_density):
        volumetric_activity = self.specific / 1000 * soil_density
        # volume of soil slice with width = 1 cm and area = 1 m^2
        volume = 100 * 100 * 1
        self.__surface = volumetric_activity * volume

    @property
    def specific(self):
        """specific activity in Bq/m^3"""
        return self.__specific

    @property
    def surface_1cm(self):
        """surface activity with surface width 1 cm in Bq/m^2
        or activity of soil slice with width = 1 cm and area = 1 m^2 in Bq
        """
        return self.__surface


class Measurement(object):
    """Holds info on activity measurement"""

    def __init__(self, activity, coo):
        self.__activity = activity
        coo.transform("EPSG:3857")
        self.__coo = coo

    @property
    def activity(self):
        return self.__activity

    @property
    def coo(self):
        return self.__coo
