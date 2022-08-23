from typing import Dict, List, Callable
from .common import pasquill_gifford_classes
import math
import numpy as np
from scipy import integrate


def effective_dose(nuclide_aclass_doses: List[Dict[str, float]]) -> float:
    """Calculate effective dose
    SM-134-17: (1), (2)

    Args:
        nuclide_aclass_doses (List[Dict[str, float]]): effective doses per
            nuclide per atmospheric class, Sv

    Returns:
        float: effective dose, Sv
    """
    aclass_doses = dict.fromkeys(pasquill_gifford_classes, 0)
    for nuclide_doses in nuclide_aclass_doses:
        for aclass in pasquill_gifford_classes:
            aclass_doses[aclass] += nuclide_doses[aclass]
    return max(aclass_doses.values())


def acute_total_effective_dose(
    nuclide: str,
    cloud_ed: float,
    inh_ed: float,
    surf_ed: float,
    nuclide_groups: Dict[str, str],
) -> float:
    """Calculate acute total effective dose due to the specific nuclide
    SM-134-17: (3)

    Args:
        nuclide (str): nuclide
        cloud_ed (float): effective dose due to radioactive cloud, Sv
        inh_ed (float): effective dose due to nuclide inhalation, Sv
        surf_ed (float): effective dose due to surface irradiation, Sv
        nuclide_groups (Dict[str, str]): dictionary of all nuclides and
            corresponding groups

    Returns:
        float: acute total effective dose due to the specific nuclide, Sv
    """
    if nuclide not in nuclide_groups.keys():
        raise ValueError(f"unknown nuclide '{nuclide}'")
    if nuclide_groups[nuclide] == "IRG":
        return cloud_ed
    else:
        return cloud_ed + inh_ed + surf_ed


def total_effective_dose_for_period(
    years: int,
    nuclide: str,
    cloud_ed: float,
    inh_ed: float,
    surf_ed: float,
    food_ed: float,
    nuclide_groups: Dict[str, str],
) -> float:
    """Calculate total effective dose due to specific nuclide for a period
    SM-134-17: (4)

    Args:
        years (int): time since accident, years
        nuclide (str): nuclide
        cloud_ed (float): effective dose due to radioactive cloud, Sv
        inh_ed (float): effective dose due to nuclide inhalation, Sv
        surf_ed (float): effective dose due to surface irradiation, Sv
        food_ed (float): effective dose due to  dietary intake, Sv
        nuclide_groups (Dict[str, str]): dictionary of all nuclides and
            corresponding groups

    Returns:
        total effective dose due to specific nuclide for a period, Sv
    """
    if nuclide not in nuclide_groups.keys():
        raise ValueError(f"unknown nuclide '{nuclide}'")
    if years <= 0:
        raise ValueError(f"invalid period '{years}'")
    if nuclide_groups[nuclide] == "IRG":
        return cloud_ed
    elif years == 1:
        return cloud_ed + inh_ed + surf_ed + food_ed
    else:
        raise NotImplementedError


def effective_dose_cloud(
    concentration_integral: float, dose_coefficient: float
) -> float:
    """Calculate effective dose due to external exposure form radioactive cloud
    SM-134-17: (5)

    Args:
        concentration_integral (float): Concentration in surface air time
            integral, Bq*s/m^3
        dose_coefficient (float): Dose conversion factor for external
            exposure from radioactive cloud, (Sv*m^3)/(Bq*s)

    Returns:
        float: effecive dose due to external exposure form radioactive cloud,
            Sv
    """
    return concentration_integral * dose_coefficient


def effective_dose_surface(
    deposition: float, dose_coefficient: float, residence_time_coeff: float
) -> float:
    """Calculate effective dose due to external exposure form contaminated soil
    SM-134-17: (6)

    Args:
        deposition (float): Summarized deposition value on ground surface due
            to dry and wet deposition, Bq/m^2
        dose_coefficient (float): Dose conversion factor for external exposure
            from soil surface, (Sv*m^2)/(Bq*s)
        residence_time_coeff (float): Residence time coefficient, s

    Returns:
        float: effective dose due to external exposure form contaminated soil,
            Sv
    """
    return deposition * dose_coefficient * residence_time_coeff


def residence_time_coeff(
    dose_rate_decay_coeff: float,
    radioactive_decay_coeff: float,
    residence_time: float,
) -> float:
    """Calculate residence time coefficient
    SM-134-17: (7)

    Args:
        dose_rate_decay_coeff (float): dose rate decay coefficient, s^-1
        radioactive_decay_coeff (float): radioactive decay coefficient, s^-1
        residence_time (float): residence time, s

    Returns:
        float: residence time coefficient, 1
    """
    decay_coeff = dose_rate_decay_coeff + radioactive_decay_coeff
    return (1 - math.exp(-decay_coeff * residence_time)) / decay_coeff


def effective_dose_inhalation(
    concentration_integral: float,
    dose_coefficient: float,
    respiration_rate: float,
) -> float:
    """Calculate effective dose due to internal exposure from inhalation
    SM-134-17: (8)

    Args:
        concentration_integral (float): Concentration in surface air time
            integral, Bq*s/m^3
        dose_coefficient (float): Dose conversion factor for internal
            exposure from inhalation, Sv/Bq
        respiration_rate (float): Respiration rate, m^3/s

    Returns:
        float: effective dose due to internal exposure from inhalation, Sv
    """
    return concentration_integral * dose_coefficient * respiration_rate


def effective_dose_food(
    dose_coefficient: float,
    food_specific_activity: Dict[str, float],
    annual_food_intake: Dict[str, float],
) -> float:
    """Calculate effective dose due to internal exposure from food intake
    SM-134-17: (9)

    Args:
        dose_coefficient (float): Dose conversion factor for internal exposure
            from food intake, Sv/Bq
        food_specific_activity (Dict[float]): Specific activities in food, key
            is food category, Bq/kg
        annual_food_intake (Dict[float]): Annual food intake, key is food
            category, kg

    Returns:
        float: effective dose due to internal exposure from food intake, Sv
    """
    if food_specific_activity.keys() != annual_food_intake.keys():
        raise ValueError(
            "inconsistent food categories: "
            f"'{food_specific_activity.keys()}' and "
            f"'{annual_food_intake.keys()}'"
        )
    summ = 0
    for food_cat in food_specific_activity:
        summ += food_specific_activity[food_cat] * annual_food_intake[food_cat]
    return dose_coefficient * summ


def annual_food_intake(
    daily_metabolic_cost: float,
    daily_metabolic_cost_adults: float,
    annual_food_intake_adults: float,
) -> float:
    """Calculate annual food intake for specific age group
    SM-134-17: (10)

    Args:
        daily_metabolic_cost (float): daily metabolic cost for age group,
            kcal/day
        daily_metabolic_cost_adults (float): daily metabolic cost for adults,
            kcal/day
        annual_food_intake_adults (float): annual food intake for adults,
            kg/year

    Returns:
        float: annual food intake, kg/year
    """
    return (
        daily_metabolic_cost
        / daily_metabolic_cost_adults
        * annual_food_intake_adults
    )


def food_max_distance(
    distances: np.array,
    doses_matrix: np.array,
    minimal_distance: float = 0,
) -> float:
    """Calculate distance with maximum food effective dose (x_max)
    SM-134-17: (11)

    Args:
        distances (np.array): set of distances from which x_max shall be
            picked up, m
        doses_matrix (np.array): three-dimensional array of effective doses,
            Sv;
            first dimension corresponds to distance from source;
            second dimension corresponds to atmospheric stability class;
            third dimension corresponds to nuclide.
        minimal_distance (float, optional): minimal value of x_max, m; it could
            be distance to buffer area, operating nuclear island, etc.

    Returns:
        float: x_max, m
    """
    if doses_matrix.shape[0] != distances.size:
        raise ValueError(
            "first matrix band should correspond to given distances "
            f"set: {doses_matrix.shape[0]} != {distances.size}"
        )
    if doses_matrix.shape[1] != len(pasquill_gifford_classes):
        raise ValueError(
            "second matrix band should correspond to atmospheric "
            f"classes: {doses_matrix.shape[1]} != "
            f"{len(pasquill_gifford_classes)}"
        )
    doses = np.full(distances.size, None)
    for i in range(distances.size):
        doses[i] = max(
            [
                sum(doses_matrix_for_aclass)
                for doses_matrix_for_aclass in doses_matrix[i]
            ]
        )
    max_dose_idx = np.where(doses == np.amax(doses))[0][-1]
    x_max = distances[max_dose_idx]
    if x_max < minimal_distance:
        x_max = minimal_distance
    return x_max


def concentration_integral(activity: float, dilution_factor: float) -> float:
    """Calculate radionuclide timed concentration integral
    SM-134-17: A1(1)

    Args:
        activity (float): accidental release radionuclide activity, Bq
        dilution_factor (float): dilution factor, s/m^3

    Returns:
        float: radionuclide timed concentration integral, Bq*s/m^3
    """
    return activity * dilution_factor


def height_dist_concentration_integral(
    activity: float, dilution_factor: float
) -> float:
    """Calculate height distributed radionuclide timed concentration integral
    SM-134-17: A1(2)

    Args:
        activity (float): accidental release radionuclide activity, Bq
        dilution_factor (float): height distributed dilution factor, s/m^2

    Returns:
        float: height distributed radionuclide timed concentration integral,
            Bq*s/m^2
    """
    return activity * dilution_factor


def deposition(
    sedimentation_rate: float,
    sediment_detachment_constant: float,
    concentration_integral: float,
    height_dist_concentration_integral: float,
) -> float:
    """Calculate deposition
    SM-134-17: A1(5)

    Args:
        sedimentation_rate (float): nuclide sedimentation rate, m/s
        sediment_detachment_constant (float): sediment detachment constant,
            s^-1
        concentration_integral (float): radionuclide timed concentration
            integral, Bq*s/m^3
        height_dist_concentration_integral (float): height distributed
            radionuclide timed concentration integral, Bq*s/m^2

    Returns:
        float: deposition, Bq/m^2
    """
    return (
        sedimentation_rate * concentration_integral
        + sediment_detachment_constant * height_dist_concentration_integral
    )


def food_specific_activity(
    sedimentation_rate: float,
    sediment_detachment_constant: float,
    concentration_integral: float,
    height_dist_concentration_integral: float,
    atmosphere_accumulation_factor: float,
    soil_accumulation_factor: float,
) -> float:
    """Calculate food specific activity
    SM-134-17: A1(6)

    Args:
        sedimentation_rate (float): nuclide sedimentation rate, m/s
        sediment_detachment_constant (float): sediment detachment constant,
            s^-1
        concentration_integral (float): radionuclide timed concentration
            integral, Bq*s/m^3
        height_dist_concentration_integral (float): height distributed
            radionuclide timed concentration integral, Bq*s/m^2
        atmosphere_accumulation_factor (float): the accumulation coefficient
            normalized for productivity "precipitation from the atmosphere -
            content in food", m^2/kg
        soil_accumulation_factor (float): the accumulation coefficient
            normalized for productivity "deposition on the soil - content in
            food", m^2/kg

    Returns:
        float: food specific activity, Bq/kg
    """
    return (
        sedimentation_rate * concentration_integral
        + 0.2
        * sediment_detachment_constant
        * height_dist_concentration_integral
    ) * atmosphere_accumulation_factor + (
        sedimentation_rate * concentration_integral
        + sediment_detachment_constant * height_dist_concentration_integral
    ) * soil_accumulation_factor


def dilution_factor(
    depletion: float,
    dispersion_coeff_y: Callable[[float], float],
    dispersion_coeff_z: Callable[[float], float],
    wind_speed: float,
    vertical_dispersion: Callable[[float, float], float],
    half_square_side: float,
    distance: float,
    terrain_clearance: float,
) -> float:
    """Calculate dilution factor
    SM-134-17: A2(11)

    Args:
        depletion (float): depletion function value, unitless
        dispersion_coeff_y (Callable[[float, ], float, ]): radioactive cloud
            dispersion coefficient for horizontal direction function, m;
            argument - distance, m
        dispersion_coeff_z (Callable[[float, ], float, ]): radioactive cloud
            dispersion coefficient for vertical direction function, m;
            argument - distance, m
        wind_speed (float): wind speed, m/s
        vertical_dispersion (Callable[[float, float], float]): vertical
            dispersion factor function, unitless;
            1st arg - terrain clearance, m;
            2nd arg - distance, m
        half_square_side (float): half of square surface source side length, m
        distance (float): distance to source, m
        terrain_clearance (float): terrain clearance, m

    Returns:
        float: dilution factor
    """
    factor = depletion / (
        math.sqrt(2 * math.pi) * wind_speed * 4 * math.pow(half_square_side, 2)
    )

    def subintegral_function(xi: float):
        arg = distance - xi
        return (
            vertical_dispersion(terrain_clearance, arg)
            / dispersion_coeff_z(arg)
            * math.erf(
                half_square_side / (math.sqrt(2) * dispersion_coeff_y(arg))
            )
        )

    return (
        factor
        * integrate.quad(
            subintegral_function, -half_square_side, half_square_side
        )[0]
    )
