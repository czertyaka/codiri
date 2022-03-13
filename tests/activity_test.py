from codri.src.activity import (
    ActivityMap,
    ExceedingStepError,
    Measurment,
    ExceedingMeasurmentProximity,
)
from codri.src.geo import Coordinate
from codri.src.basins import Basin
import numpy as np
import pytest


def test_measurment():
    measurment = Measurment(
        activity=0, coo=Coordinate(lon=10, lat=10, crs="EPSG:4326")
    )
    assert measurment.coo.crs == "EPSG:3857"


def check_empty_map(ul, lr, new_lr, step, ref_width, ref_height):
    actmap = ActivityMap(ul=ul, lr=lr, step=step).img
    assert actmap.width == ref_width
    assert actmap.height == ref_height
    assert actmap.xy(0, 0, offset="ul") == (ul.lon, ul.lat)
    assert actmap.xy(actmap.width, actmap.height, offset="ul") == (
        new_lr.lon,
        new_lr.lat,
    )

    data = actmap.read(1)
    unique_values = np.unique(data)
    assert unique_values.size == 1
    assert unique_values[0] == 0


def test_map():
    lr = Coordinate(lon=20, lat=10)
    check_empty_map(
        ul=Coordinate(lon=10, lat=20),
        lr=lr,
        new_lr=lr,
        step=1,
        ref_width=10,
        ref_height=10,
    )


def test_map_large_step():
    check_empty_map(
        ul=Coordinate(lon=10, lat=20),
        lr=Coordinate(lon=25, lat=5),
        new_lr=Coordinate(lon=20, lat=10),
        step=10,
        ref_width=1,
        ref_height=1,
    )


def test_map_exceeding_step():
    ul = Coordinate(lon=10, lat=20)
    lr = Coordinate(lon=25, lat=5)
    with pytest.raises(ExceedingStepError):
        ActivityMap(ul, lr, 100)


def check_adding_basin(
    basins_with_measurments, ref_data, resolution, measurment_proximity=0
):
    actmap = ActivityMap(
        ul=Coordinate(lon=0, lat=resolution),
        lr=Coordinate(lon=resolution, lat=0),
        step=1,
    )
    actmap.measurment_proximity = measurment_proximity
    for dictionary in basins_with_measurments:
        basin = Basin(contour=dictionary["basin_cnt"])
        actmap.add_basin(basin=basin, measurments=dictionary["measurments"])
    data = actmap.img.read(1)
    assert (data == ref_data).all()


#         * *
#         1 *
# - - - -
# - - - -
# - - - -
# - - - -
def test_add_outer_basin():
    res = 4
    check_adding_basin(
        basins_with_measurments=[
            {
                "basin_cnt": [[4, 4], [4, 5], [5, 5], [5, 4]],
                "measurments": [Measurment(activity=1, coo=Coordinate(4, 4))],
            }
        ],
        ref_data=np.zeros((res, res)).astype("uint8"),
        resolution=res,
    )


# - - - -
# - * * -
# - * * -
# - - - -
def test_add_basin_with_no_measurments():
    res = 4
    check_adding_basin(
        basins_with_measurments=[
            {
                "basin_cnt": [[1, 1], [2, 1], [2, 2], [1, 2]],
                "measurments": [],
            }
        ],
        ref_data=np.zeros((res, res)).astype("uint8"),
        resolution=res,
    )


# - - - -
# - * * -
# - 0 * -
# - - - -
def test_add_basin_with_zero_measurments():
    res = 4
    check_adding_basin(
        basins_with_measurments=[
            {
                "basin_cnt": [[1, 1], [2, 1], [2, 2], [1, 2]],
                "measurments": [Measurment(activity=0, coo=Coordinate(1, 1))],
            }
        ],
        ref_data=np.zeros((res, res)).astype("uint8"),
        resolution=res,
    )


# - - - -
# - * * -
# - 1 * -
# - - - -
def test_add_basin():
    res = 4
    check_adding_basin(
        basins_with_measurments=[
            {
                "basin_cnt": [[1, 1], [2, 1], [2, 2], [1, 2]],
                "measurments": [Measurment(activity=1, coo=Coordinate(1, 1))],
            }
        ],
        ref_data=np.array(
            [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]
        ).astype("uint8"),
        resolution=res,
    )


#     * * *
# - - * - *
# - - 1 * *
# - - - -
# - - - -
def test_add_partly_inner_basin():
    res = 4
    check_adding_basin(
        basins_with_measurments=[
            {
                "basin_cnt": [[2, 2], [4, 2], [4, 4], [2, 4]],
                "measurments": [Measurment(activity=1, coo=Coordinate(2, 2))],
            }
        ],
        ref_data=np.array(
            [[0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]]
        ).astype("uint8"),
        resolution=res,
    )


#           *
#   - - - * *
#   - - * - *
#   - * - - *
#   1 - - - *
# * * * * * *
def test_add_partly_inner_basin_with_no_inner_points():
    res = 4
    check_adding_basin(
        basins_with_measurments=[
            {
                "basin_cnt": [[-1, -1], [4, -1], [4, 4]],
                "measurments": [Measurment(activity=1, coo=Coordinate(0, 0))],
            }
        ],
        ref_data=np.array(
            [[0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]]
        ).astype("uint8"),
        resolution=res,
    )


#     * * *
# - - * - *
# * - 2 * *
# * * - -
# 1 * * -
def test_add_few_basins():
    res = 4
    check_adding_basin(
        basins_with_measurments=[
            {
                "basin_cnt": [[0, 0], [2, 0], [0, 2]],
                "measurments": [Measurment(activity=1, coo=Coordinate(0, 0))],
            },
            {
                "basin_cnt": [[2, 2], [4, 2], [4, 4], [2, 4]],
                "measurments": [Measurment(activity=2, coo=Coordinate(2, 2))],
            },
        ],
        ref_data=np.array(
            [[0, 0, 2, 0], [1, 0, 2, 2], [1, 1, 0, 0], [1, 1, 1, 0]]
        ).astype("uint8"),
        resolution=res,
    )


# - - - -
# - * 3 -
# - 1 * -
# - - - -
def test_add_basin_with_few_measurments():
    res = 4
    check_adding_basin(
        basins_with_measurments=[
            {
                "basin_cnt": [[1, 1], [1, 2], [2, 2], [2, 1]],
                "measurments": [
                    Measurment(activity=1, coo=Coordinate(1, 1)),
                    Measurment(activity=3, coo=Coordinate(2, 2)),
                ],
            }
        ],
        ref_data=np.array(
            [[0, 0, 0, 0], [0, 2, 3, 0], [0, 1, 2, 0], [0, 0, 0, 0]]
        ).astype("uint8"),
        resolution=res,
    )


# - - - 1
# * - - -
# * * - -
# * * * -
def test_add_basin_with_too_far_measurment():
    with pytest.raises(ExceedingMeasurmentProximity):
        res = 4
        actmap = ActivityMap(
            ul=Coordinate(0, res), lr=Coordinate(res, 0), step=1
        )
        actmap.measurment_proximity = 1
        actmap.add_basin(
            basin=Basin(contour=[[0, 2], [0, 0], [2, 0]]),
            measurments=[Measurment(activity=1, coo=Coordinate(3, 3))],
        )


# - - - 1
# * - - -
# * * - -
# * * * -
def test_add_basin_with_close_enough_measurment():
    res = 4
    check_adding_basin(
        basins_with_measurments=[
            {
                "basin_cnt": [[0, 0], [0, 3], [3, 0]],
                "measurments": [Measurment(activity=1, coo=Coordinate(3, 3))],
            }
        ],
        ref_data=np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        ).astype("uint8"),
        resolution=res,
        measurment_proximity=3,
    )
