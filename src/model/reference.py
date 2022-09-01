from ..database import Database
from dataset import Table
from typing import Dict, Tuple


class IReference:

    """Reference abstract interface class, provides access to a set of values
    and tables which serves as reference data and must be initialized by the
    inherit
    """

    def __init__(self):
        """IReference constructor"""
        self._dose_rate_decay_coeff = None
        self._residence_time = None
        self._unitless_washing_capacity = None
        self._terrain_clearance = None
        self._mixing_layer_height = None
        self._age_groups = {}
        self._diffusion_coefficients = {}
        self._nuclides = {}
        self._roughness = {}
        self._initialize_data()

    def _initialize_data(self):
        """Initialize data

        Raises:
            NotImplementedError: always
        """
        raise NotImplementedError

    @property
    def dose_rate_decay_coeff(self) -> float:
        """Get dose rate decay coefficient due to all processes except
        radioactivity decay

        Returns:
            float: dose rate decay coefficient, s^-1
        """
        return self._dose_rate_decay_coeff

    @property
    def residence_time(self) -> float:
        """Get population residence time in contaminated region for acute phase
        of a radiation accident

        Returns:
            float: residence time, s
        """
        return self._residence_time

    @property
    def unitless_washing_capacity(self) -> float:
        """Get unitless washing capacity for other precipitation types

        Returns:
            float: unitless washing capacity, unitless
        """
        return self._unitless_washing_capacity

    @property
    def terrain_clearance(self) -> float:
        """Get terrain clearance

        Returns:
            float: terrain clearance, m
        """
        return self._terrain_clearance

    @property
    def mixing_layer_height(self) -> float:
        """Get mixing layer height

        Returns:
            float: mixing layer height, m
        """
        return self._mixing_layer_height

    @property
    def nuclides(self) -> Tuple[str]:
        """Get set of all nuclides known by reference data

        Returns:
            Tuple[str]: set if nuclides
        """
        return tuple(self._nuclides.keys())

    def nuclide_decay_coeff(self, nuclide: str) -> float:
        """Get radioactivity decay coefficient

        Args:
            nuclide (str): nuclide name

        Returns:
            float: radioactivity decay coefficient, s^-1
        """
        return self._nuclides[nuclide]["decay_coeff"]

    def nuclide_group(self, nuclide: str) -> str:
        """Get nuclide group, e.g. aerosol, IRG etc.

        Args:
            nuclide (str): nuclide name

        Returns:
            str: nuclide group
        """
        return self._nuclides[nuclide]["group"]

    def cloud_dose_coeff(self, nuclide: str) -> float:
        """Get dose conversion factor for external exposure from radioactive
        cloud

        Args:
            nuclide (str): nuclide name

        Returns:
            float: dose conversion factor, (Sv*m^3)/(Bq*s)
        """
        return self._nuclides[nuclide]["R_cloud"]

    def inhalation_dose_coeff(self, nuclide: str) -> float:
        """Get dose conversion factor for nuclide intake with air

        Args:
            nuclide (str): nuclide name

        Returns:
            float: dose conversion factor, Sv/Bq
        """
        return self._nuclides[nuclide]["R_inh"]

    def surface_dose_coeff(self, nuclide: str) -> float:
        """Get dose conversion factor for external exposure from soil surface

        Args:
            nuclide (str): nuclide name

        Returns:
            float: dose conversion factor ,(Sv*m^2)/(Bq*s)
        """
        return self._nuclides[nuclide]["R_surface"]

    def respiration_rate(self, age: int) -> float:
        """Get respiration rate

        Args:
            age (int): age

        Returns:
            float: respiration rate, m^3/s
        """
        return self._age_groups[self._group_id(age)]["respiration_rate"]

    def deposition_rate(self, nuclide: str) -> float:
        """Get deposition rate

        Args:
            nuclide (str): nuclide name

        Returns:
            float: deposition rate, m/s
        """
        return self._nuclides[nuclide]["deposition_rate"]

    def standard_washing_capacity(self, nuclide: str) -> float:
        """Get standard washing capacity

        Args:
            nuclide (str): nuclide name

        Returns:
            float: standard washing capacity, hr/(mm*s)
        """
        return self._nuclides[nuclide]["standard_washing_capacity"]

    def terrain_roughness(self, terrain_type: str) -> float:
        """Get underlying terrain roughness, m

        Args:
            terrain_type (str): terrain type

        Returns:
            float: terrain roughness, m
        """
        return self._roughness[terrain_type]["roughness"]

    def diffusion_coefficients(self, a_class: str) -> Dict[str, float]:
        """Diffusion coefficients p_z, q_z, p_y and q_y for release
        height < 50 m

        Args:
            a_class (str): atmospheric stability class

        Returns:
            Dict[str, float]: diffusion coefficients, dimension unknown
                keys: 'p_z', 'q_z', 'p_y' and 'q_y'
        """
        return self._diffusion_coefficients[a_class]

    def _group_id(self, age: int) -> int:
        """Get age group if by age

        Args:
            age (int): age

        Returns:
            int: age group id

        Raises:
            ValueError: age fits no known age group
        """
        for group_id in self._age_groups:
            if (
                age >= self._age_groups[group_id]["lower_age"]
                and age < self._age_groups[group_id]["upper_age"]
            ):
                return group_id
        raise ValueError(f"invalid age '{age}'")


class Reference(IReference):

    """Concrete reference class which initializes all the values and tables"""

    def __init__(self, db: Database):
        """Reference constructor

        Args:
            db (Database): database to load tables from
        """
        super(Reference, self).__init__()
        self._db = db

    def _initialize_data(self):
        """Initialize data"""
        self._init_constant_values()
        self._init_tables(self._db)
        self._db = None

    def _init_constant_values(self):
        """Initialize constant values"""
        self._dose_rate_decay_coeff = 1.27e-9
        self._residence_time = 3.15e7
        self._unitless_washing_capacity = 5.0
        self._terrain_clearance = 1.0
        self._mixing_layer_height = 100.0

    def _init_tables(self, db: Database):
        """Initialize tables

        Args:
            db (Database): database to load tables from
        """
        self._load_age_groups(db)
        self._load_diffusion_coefficients(db)
        self._load_nuclides(db)
        self._load_roughness(db)

    def _load_table_to_dict(
        self, table: Table, table_primary_key: str, out_dict: Dict
    ):
        """Load database table to a dictionary

        Args:
            table (Table): database table
            table_primary_key (str): table's primary key (also a key for output
                dict)
            out_dict (Dict): output dictionary
        """
        for record in table:
            out_dict[record[table_primary_key]] = {
                key: record[key] for key in record if key != table_primary_key
            }

    def _load_age_groups(self, db: Database):
        """Load age groups table

        Args:
            db (Database): database to load table from
        """
        self._load_table_to_dict(
            db.load_table("age_groups"), "id", self._age_groups
        )

    def _load_diffusion_coefficients(self, db: Database):
        """Load diffusion coefficients table

        Args:
            db (Database): database to load table from
        """
        self._load_table_to_dict(
            db.load_table("diffusion_coefficients"),
            "a_class",
            self._diffusion_coefficients,
        )

    def _load_nuclides(self, db: Database):
        """Load nuclides table

        Args:
            db (Database): database to load tables from
        """
        self._load_table_to_dict(
            db.load_table("nuclides"), "name", self._nuclides
        )

    def _load_roughness(self, db: Database):
        """Load roughness table

        Args:
            db (Database): database to load tables from
        """
        self._load_table_to_dict(
            db.load_table("roughness"), "terrain", self._roughness
        )
