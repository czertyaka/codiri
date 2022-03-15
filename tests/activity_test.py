from codri.src.activity import (
    ActivityMap,
    ExceedingStepError,
    ExceedingMeasurementProximity,
    InvalidMeasurementLocation,
)
from codri.src.measurement import Measurement, SoilActivity
from codri.src.geo import Coordinate
from codri.src.basins import Basin
import numpy as np
import pytest


def check_empty_map(ul, lr, new_lr, step, ref_width, ref_height):
    actmap = ActivityMap(ul=ul, lr=lr, step=step).img
    assert actmap.width == ref_width
    assert actmap.height == ref_height
    assert actmap.index(ul.lon, ul.lat) == (0, 0)
    assert actmap.index(new_lr.lon, new_lr.lat) == (
        actmap.width - 1,
        actmap.height - 1,
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
        ref_width=11,
        ref_height=11,
    )


def test_map_large_step():
    check_empty_map(
        ul=Coordinate(lon=10, lat=20),
        lr=Coordinate(lon=25, lat=5),
        new_lr=Coordinate(lon=20, lat=10),
        step=11,
        ref_width=1,
        ref_height=1,
    )


def test_map_exceeding_step():
    ul = Coordinate(lon=10, lat=20)
    lr = Coordinate(lon=25, lat=5)
    with pytest.raises(ExceedingStepError):
        ActivityMap(ul, lr, 100)


def check_adding_basin(
    basins_with_measurements,
    ref_data_normalized,
    resolution,
    measurement_proximity=0,
    shoreline_width=1,
    crop_basin=False,
):
    last_idx = resolution - 1
    actmap = ActivityMap(
        ul=Coordinate(lon=0, lat=last_idx),
        lr=Coordinate(lon=last_idx, lat=0),
        step=1,
    )
    actmap.measurement_proximity = measurement_proximity
    for dictionary in basins_with_measurements:
        basin = Basin(
            contour=dictionary["basin_cnt"],
            shoreline_width=shoreline_width,
            map_contour=[
                [0, 0],
                [0, last_idx],
                [last_idx, last_idx],
                [last_idx, 0],
            ]
            if crop_basin is True
            else None,
        )
        actmap.add_basin(basin=basin, measurements=dictionary["measurements"])
    data = actmap.img.read(1)
    assert data.shape == ref_data_normalized.shape
    assert (data == ref_data_normalized).all()


#         * *
#         1 *
# - - - -
# - - - -
# - - - -
# - - - -
def test_add_outer_basin():
    res = 4
    check_adding_basin(
        basins_with_measurements=[
            {
                "basin_cnt": [[4, 4], [4, 5], [5, 5], [5, 4]],
                "measurements": [
                    Measurement(activity=SoilActivity(1), coo=Coordinate(4, 4))
                ],
            }
        ],
        ref_data_normalized=np.zeros((res, res)).astype("uint8"),
        resolution=res,
    )


# - - - -
# - * * -
# - * * -
# - - - -
def test_add_basin_with_no_measurements():
    res = 4
    check_adding_basin(
        basins_with_measurements=[
            {
                "basin_cnt": [[1, 1], [2, 1], [2, 2], [1, 2]],
                "measurements": [],
            }
        ],
        ref_data_normalized=np.zeros((res, res)).astype("uint8"),
        resolution=res,
    )


# - - - -
# - * * -
# - 0 * -
# - - - -
def test_add_basin_with_zero_measurements():
    res = 4
    check_adding_basin(
        basins_with_measurements=[
            {
                "basin_cnt": [[1, 1], [2, 1], [2, 2], [1, 2]],
                "measurements": [
                    Measurement(activity=SoilActivity(0), coo=Coordinate(1, 1))
                ],
            }
        ],
        ref_data_normalized=np.zeros((res, res)).astype("uint8"),
        resolution=res,
    )


# - - - -
# - * * -
# - 1 * -
# - - - -
def test_add_basin():
    res = 4
    check_adding_basin(
        basins_with_measurements=[
            {
                "basin_cnt": [[1, 1], [2, 1], [2, 2], [1, 2]],
                "measurements": [
                    Measurement(activity=SoilActivity(1), coo=Coordinate(1, 1))
                ],
            }
        ],
        ref_data_normalized=np.array(
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
        basins_with_measurements=[
            {
                "basin_cnt": [[2, 2], [4, 2], [4, 4], [2, 4]],
                "measurements": [
                    Measurement(activity=SoilActivity(1), coo=Coordinate(2, 2))
                ],
            }
        ],
        ref_data_normalized=np.array(
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
        basins_with_measurements=[
            {
                "basin_cnt": [[-1, -1], [4, -1], [4, 4]],
                "measurements": [
                    Measurement(activity=SoilActivity(1), coo=Coordinate(0, 0))
                ],
            }
        ],
        ref_data_normalized=np.array(
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
        basins_with_measurements=[
            {
                "basin_cnt": [[0, 0], [2, 0], [0, 2]],
                "measurements": [
                    Measurement(activity=SoilActivity(1), coo=Coordinate(0, 0))
                ],
            },
            {
                "basin_cnt": [[2, 2], [4, 2], [4, 4], [2, 4]],
                "measurements": [
                    Measurement(activity=SoilActivity(2), coo=Coordinate(2, 2))
                ],
            },
        ],
        ref_data_normalized=np.array(
            [
                [0, 0, 1, 0],
                [0.5, 0, 1, 1],
                [0.5, 0.5, 0, 0],
                [0.5, 0.5, 0.5, 0],
            ]
        ).astype("uint8"),
        resolution=res,
    )


# - - - -
# - * 3 -
# - 1 * -
# - - - -
def test_add_basin_with_few_measurements():
    res = 4
    check_adding_basin(
        basins_with_measurements=[
            {
                "basin_cnt": [[1, 1], [1, 2], [2, 2], [2, 1]],
                "measurements": [
                    Measurement(
                        activity=SoilActivity(1), coo=Coordinate(1, 1)
                    ),
                    Measurement(
                        activity=SoilActivity(3), coo=Coordinate(2, 2)
                    ),
                ],
            }
        ],
        ref_data_normalized=np.array(
            [[0, 0, 0, 0], [0, 0.67, 1, 0], [0, 0.33, 0.67, 0], [0, 0, 0, 0]]
        ).astype("uint8"),
        resolution=res,
    )


# - - - 1
# * - - -
# * * - -
# * * * -
def test_add_basin_with_too_far_measurement():
    with pytest.raises(ExceedingMeasurementProximity):
        res = 4
        actmap = ActivityMap(
            ul=Coordinate(0, res), lr=Coordinate(res, 0), step=1
        )
        actmap.measurement_proximity = 1
        actmap.add_basin(
            basin=Basin(contour=[[0, 2], [0, 0], [2, 0]]),
            measurements=[
                Measurement(activity=SoilActivity(1), coo=Coordinate(3, 3))
            ],
        )


# - - - 1
# * - - -
# * * - -
# * * * -
def test_add_basin_with_close_enough_measurement():
    res = 4
    check_adding_basin(
        basins_with_measurements=[
            {
                "basin_cnt": [[0, 0], [0, 3], [3, 0]],
                "measurements": [
                    Measurement(activity=SoilActivity(1), coo=Coordinate(3, 3))
                ],
            }
        ],
        ref_data_normalized=np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        ).astype("uint8"),
        resolution=res,
        measurement_proximity=3,
    )


# - - - -
# * * * -
# * 1 * -
# * * * -
def test_add_basin_invalid_measurement_location():
    with pytest.raises(InvalidMeasurementLocation):
        res = 4
        actmap = ActivityMap(
            ul=Coordinate(0, res), lr=Coordinate(res, 0), step=1
        )
        actmap.measurement_proximity = 1
        actmap.add_basin(
            basin=Basin(contour=[[0, 0], [2, 0], [2, 2], [0, 2]]),
            measurements=[
                Measurement(activity=SoilActivity(1), coo=Coordinate(1, 1))
            ],
        )


# - 1 - -
# - * * *
# - * * *
# - * * 1
def test_add_basin_measurmentes_for_all_segments():
    res = 4
    check_adding_basin(
        basins_with_measurements=[
            {
                "basin_cnt": [[1, 0], [1, 2], [3, 2], [3, 1], [2, 1], [2, 0]],
                "measurements": [
                    Measurement(
                        activity=SoilActivity(1), coo=Coordinate(3, 0)
                    ),
                    Measurement(
                        activity=SoilActivity(2), coo=Coordinate(1, 3)
                    ),
                ],
            }
        ],
        ref_data_normalized=np.array(
            [[0, 0, 0, 0], [0, 1, 1, 1], [0, 1, 0.5, 0.5], [0, 1, 0.5, 0]]
        ).astype("uint8"),
        resolution=res,
        measurement_proximity=1,
        crop_basin=True,
    )


# - - - -
# - * * *
# - * * *
# - * * 1
def test_add_basin_measurmentes_for_some_segments():
    res = 4
    check_adding_basin(
        basins_with_measurements=[
            {
                "basin_cnt": [[1, 0], [1, 2], [3, 2], [3, 1], [2, 1], [2, 0]],
                "measurements": [
                    Measurement(
                        activity=SoilActivity(1), coo=Coordinate(3, 0)
                    ),
                ],
            }
        ],
        ref_data_normalized=np.array(
            [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 1, 1], [0, 0, 1, 0]]
        ).astype("uint8"),
        resolution=res,
        measurement_proximity=1,
        crop_basin=True,
    )


# 1 - - -
# - * * *
# - * * *
# - * * 1
def test_add_basin_measurmentes_far_from_segment():
    res = 4
    check_adding_basin(
        basins_with_measurements=[
            {
                "basin_cnt": [[1, 0], [1, 2], [3, 2], [3, 1], [2, 1], [2, 0]],
                "measurements": [
                    Measurement(
                        activity=SoilActivity(1), coo=Coordinate(3, 0)
                    ),
                    Measurement(
                        activity=SoilActivity(1), coo=Coordinate(0, 3)
                    ),
                ],
            }
        ],
        ref_data_normalized=np.array(
            [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 1, 1], [0, 0, 1, 0]]
        ).astype("uint8"),
        resolution=res,
        measurement_proximity=1,
        crop_basin=True,
    )
