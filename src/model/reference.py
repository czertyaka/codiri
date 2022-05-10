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

    def radio_decay_coeff(self, nuclide: str) -> float:
        """Radioactivity decay coefficient, sec^-1"""
        return float(self.__find_nuclide(nuclide)["decay_coeff"])

    @property
    def dose_rate_decay_coeff(self) -> float:
        """Dose rate decay coefficient due to all processes except
        radioactivity decay, sec^-1
        """
        return 1.27e-9

    @property
    def residence_time(self) -> float:
        """Population residence time in contaminated region for acute phase of
        a radiation accident, sec
        """
        return 3.15e7

    def nuclide_group(self, nuclide: str) -> str:
        """Nuclide group, e.g. aerosol, IRG etc."""
        return str(self.__find_nuclide(nuclide)["group"])

    def cloud_dose_coeff(self, nuclide: str) -> float:
        """Dose conversion factor for external exposure from radioactive cloud,
        (Sv*m^3)/(Bq*s)
        """
        return float(self.__find_nuclide(nuclide)["R_cloud"])

    def inhalation_dose_coeff(self, nuclide: str) -> float:
        """Dose conversion factor for nuclide intake with air, Sv/Bq"""
        return float(self.__find_nuclide(nuclide)["R_inh"])

    def surface_dose_coeff(self, nuclide: str) -> float:
        """Dose conversion factor for external exposure from soil surface,
        (Sv*m^2)/(Bq*s)
        """
        return float(self.__find_nuclide(nuclide)["R_surface"])

    def respiration_rate(self, age: int) -> float:
        """Respiration rate, m^3/sec"""
        rate = self.db["age_groups"].find_one(id=self.__get_age_group_id(age))[
            "respiration_rate"
        ]
        return float(rate)

    def deposition_rate(self, nuclide: str) -> float:
        """Deposition rate, m/s"""
        return float(self.__find_nuclide(nuclide)["deposition_rate"])

    def standard_washing_capacity(self, nuclide: str) -> float:
        """Standard washing capacity, hr/(mm*sec)"""
        return 0 if self.__find_nuclide(nuclide)["group"] == "IRG" else 1e-5

    @property
    def unitless_washing_capacity(self) -> float:
        """Unitless washing capacity for other precipitation types, 1"""
        return 5.0

    def terrain_roughness(self, terrain_type: str) -> float:
        """Underlying terrain roughness, m"""
        return self.db.load_table("roughness").find_one(terrain=terrain_type)[
            "roughness"
        ]

    def diffusion_coefficients(self, atmospheric_class: str) -> dict:
        """Diffusion coefficients p_z, q_z, p_y and q_y for release
        height < 50 m
        :return: dict with keys 'p_z', 'q_z', 'p_y' and 'q_y'
        """
        coeffs = dict(
            self.db.load_table("diffusion_coefficients").find_one(
                a_class=atmospheric_class
            )
        )
        coeffs.pop("a_class")
        return coeffs

    @property
    def terrain_clearance(self) -> float:
        """Terrain clearance, m"""
        return 1

    @property
    def mixing_layer_height(self) -> float:
        """Mixing layer height, m"""
        return 100

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
