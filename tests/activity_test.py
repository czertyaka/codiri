from codiri.src.activity import (
    ActivityMap,
    ExceedingStepError,
    ExceedingMeasurementProximity,
    InvalidMeasurementLocation,
)
from codiri.src.measurement import Measurement, SoilActivity
from codiri.src.geo import Coordinate
from codiri.src.basins import Basin
import numpy as np
import pytest


def act_map(ul, lr, step):
    return ActivityMap(ul, lr, step, None)


def check_empty_map(ul, lr, new_lr, step, ref_width, ref_height):
    actmap = act_map(ul=ul, lr=lr, step=step).img
    assert actmap.width == ref_width
    assert actmap.height == ref_height
    assert actmap.index(ul.lon + step / 2, ul.lat - step / 2) == (0, 0)
    assert actmap.index(new_lr.lon - step / 2, new_lr.lat + step / 2) == (
        actmap.width - 1,
        actmap.height - 1,
    )
    assert actmap.xy(0, 0) == (ul.lon + step / 2, ul.lat - step / 2)
    assert actmap.xy(actmap.width - 1, actmap.height - 1) == (
        new_lr.lon - step / 2,
        new_lr.lat + step / 2,
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
        act_map(ul, lr, 100)


def check_adding_basin(
    basins_with_measurements,
    ref_data_normalized,
    resolution,
    measurement_proximity=0,
    shoreline_width=1,
    crop_basin=False,
):
    last_idx = resolution - 1
    step = 1
    ul = Coordinate(lon=0 - step / 2, lat=last_idx + step / 2)
    lr = Coordinate(lon=last_idx + step / 2, lat=0 - step / 2)
    actmap = act_map(ul=ul, lr=lr, step=step)
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
    ref_data = (
        ref_data_normalized
        * (data.max() if data.max() != 0 else np.iinfo(np.uint16).max)
    ).astype(np.uint16)
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
        basins_with_measurements=[
            {
                "basin_cnt": [[4, 4], [4, 5], [5, 5], [5, 4]],
                "measurements": [
                    Measurement(activity=SoilActivity(1), coo=Coordinate(4, 4))
                ],
            }
        ],
        ref_data_normalized=np.zeros((res, res)),
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
        ref_data_normalized=np.zeros((res, res)),
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
        ref_data_normalized=np.zeros((res, res)),
        resolution=res,
    )


# - - - -
# - * * -
# - 1 * -
# - - - -
def test_add_basin_simple():
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
        ),
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
        ),
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
    magic_number = 0.273459
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
            [
                [0, 0, magic_number, 1],
                [0, magic_number, 1, magic_number],
                [magic_number, 1, magic_number, 0],
                [1, magic_number, 0, 0],
            ]
        ),
        resolution=res,
    )


#       * * *
#   - - * - *
#   - - 2 * *
# * * 1 - -
# * - * - -
# * * *
def test_add_few_basins():
    res = 4
    check_adding_basin(
        basins_with_measurements=[
            {
                "basin_cnt": [[-1, -1], [-1, 1], [1, 1], [1, -1]],
                "measurements": [
                    Measurement(activity=SoilActivity(1), coo=Coordinate(1, 1))
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
                [0, 0, 1, 1],
                [0.5, 0.5, 0, 0],
                [0, 0.5, 0, 0],
            ]
        ),
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
            [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]
        ),
        resolution=res,
    )


# - - - 1
# * - - -
# * * - -
# * * * -
def test_add_basin_with_too_far_measurement():
    with pytest.raises(ExceedingMeasurementProximity):
        res = 4
        actmap = act_map(ul=Coordinate(0, res), lr=Coordinate(res, 0), step=1)
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
        ),
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
        actmap = act_map(ul=Coordinate(0, res), lr=Coordinate(res, 0), step=1)
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
        ),
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
        ),
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
        ),
        resolution=res,
        measurement_proximity=1,
        crop_basin=True,
    )


def test_contamination_depth():
    map_size = 4
    step = 1
    actmap = act_map(
        ul=Coordinate(0, map_size - 1),
        lr=Coordinate(map_size - 1, 0),
        step=step,
    )
    activity = SoilActivity(1)
    pix_area = step * step
    depth = 1
    pix_value = activity.surface_1cm * depth * pix_area
    actmap.contamination_depth = depth
    actmap.add_basin(
        Basin(contour=[[0, 0], [1, 0], [0, 1]], shoreline_width=1),
        [Measurement(activity=activity, coo=Coordinate(1, 1))],
    )
    data = actmap.img.read(1)
    assert data[0, 0] == pix_value

    depth = 5
    pix_value = activity.surface_1cm * depth * pix_area
    actmap.contamination_depth = depth
    actmap.add_basin(
        Basin([[2, 3], [3, 3], [3, 2]]),
        [Measurement(activity=activity, coo=Coordinate(1, 1))],
    )
    data = actmap.img.read(1)
    assert data[3, 3] == pix_value


def test_shoreline_width():
    map_size = 12
    step = 1
    actmap = act_map(
        ul=Coordinate(0, map_size - 1),
        lr=Coordinate(map_size - 1, 0),
        step=step,
    )
    activity = SoilActivity(1)
    pix_area = step * step
    pix_value = activity.surface_1cm * actmap.contamination_depth * pix_area
    actmap.add_basin(
        Basin(contour=[[1, 1], [1, 4], [4, 4], [4, 1]], shoreline_width=1),
        [Measurement(activity=activity, coo=Coordinate(1, 1))],
    )
    actmap.add_basin(
        Basin(contour=[[7, 7], [7, 10], [10, 10], [10, 7]], shoreline_width=1),
        [Measurement(activity=activity, coo=Coordinate(1, 1))],
    )
    ref_data = (
        np.array(
            [
                [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            ]
        ).astype(np.uint16)
        * pix_value
    )
    data = actmap.img.read(1)
    assert data.shape == ref_data.shape
    assert (data == ref_data).all()


def test_measurments_averaging():
    map_size = 4
    step = 1
    actmap1 = act_map(
        ul=Coordinate(0, map_size - 1),
        lr=Coordinate(map_size - 1, 0),
        step=step,
    )
    actmap2 = actmap1

    basin = Basin(contour=[[1, 1], [1, 2], [2, 2], [2, 1]], shoreline_width=1)
    actmap1.add_basin(
        basin,
        [
            Measurement(activity=SoilActivity(1), coo=Coordinate(1, 1)),
            Measurement(activity=SoilActivity(3), coo=Coordinate(2, 2)),
        ],
    )
    actmap2.add_basin(
        basin, [Measurement(activity=SoilActivity(2), coo=Coordinate(1, 1))]
    )

    data1 = actmap1.img.read(1)
    data2 = actmap2.img.read(1)

    assert data1.shape == data2.shape
    assert (data1 == data2).all()
