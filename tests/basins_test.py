from codiri.src.basins import (
    BasinsFinder,
    Basin,
)
from codiri.src.geo import Coordinate
from codiri.tests.mock import MockMap
import pytest
from shapely import geometry


def test_shoreline_width():
    assert Basin(contour=[]).shoreline_width == 2
    assert Basin(contour=[], shoreline_width=3).shoreline_width == 3


# test input is small map 4x4 pix map
#
#     0 2 4 6
#    _________
#   0|* * * *|
#   2|* * * *|
#   4|* * * *|
#   6|* * * *|
#    ---------


def check_basin(
    contour, map_contour, ref_body, ref_shoreline_segments, ref_closed
):
    basin = Basin(
        contour=contour,
        map_contour=map_contour,
    )
    if basin.body.is_valid:
        assert basin.body.equals(ref_body)
    else:
        assert basin.body.boundary == ref_body.boundary
    assert basin.body.geom_type == ref_body.geom_type
    assert basin.shoreline_segments_count == len(ref_shoreline_segments)
    for i in range(basin.shoreline_segments_count):
        assert basin.shoreline[i].equals(ref_shoreline_segments[i])
        assert (
            basin.shoreline[i].geom_type == ref_shoreline_segments[i].geom_type
        )
    assert basin.is_closed == ref_closed


# - - - -
# - + + -
# - + + -
# - - - -
def test_inner_basin():
    contour = [[2, 2], [2, 4], [4, 4], [4, 2]]
    check_basin(
        contour=contour,
        map_contour=[[0, 0], [0, 6], [6, 6], [6, 0]],
        ref_body=geometry.Polygon(contour),
        ref_shoreline_segments=[geometry.LinearRing(contour)],
        ref_closed=True,
    )


# - - - -
# + + - -
# - + - -
# - - - -
def test_touching_basin():
    contour = [[0, 2], [2, 2], [2, 4]]
    check_basin(
        contour=contour,
        map_contour=[[0, 0], [0, 6], [6, 6], [6, 0]],
        ref_body=geometry.Polygon(contour),
        ref_shoreline_segments=[geometry.LinearRing(contour)],
        ref_closed=True,
    )


# - - - -
# + + + -
# - + + -
# - - + -
def test_touching_basin_few_points():
    contour = [[0, 2], [4, 2], [4, 6]]
    check_basin(
        contour=contour,
        map_contour=[[0, 0], [0, 6], [6, 6], [6, 0]],
        ref_body=geometry.Polygon(contour),
        ref_shoreline_segments=[geometry.LinearRing(contour)],
        ref_closed=True,
    )


# + + + -
# + + - -
# + - - -
# - - - -
def test_adjoining_basin():
    contour = [[0, 0], [0, 4], [4, 0]]
    check_basin(
        contour=contour,
        map_contour=[[0, 0], [0, 6], [6, 6], [6, 0]],
        ref_body=geometry.Polygon(contour),
        ref_shoreline_segments=[geometry.LineString([[0, 4], [4, 0]])],
        ref_closed=False,
    )


# + + + +
# + + + +
# + + + +
# + + + +
def test_fitting_basin():
    map_cnt = [[0, 0], [0, 6], [6, 6], [6, 0]]
    with pytest.raises(ValueError):
        Basin(contour=map_cnt, map_contour=map_cnt)


# + + + +
# + + + +
# + + + +
# + + + +
def test_overlapping_basin():
    with pytest.raises(ValueError):
        Basin(
            contour=[[-1, -1], [-1, 7], [7, 7], [7, -1]],
            map_contour=[[0, 0], [0, 6], [6, 6], [6, 0]],
        )


# + - - +
# + + + +
# + + + +
# + - - +
def test_self_intersecting_basin():
    contour = [[0, 0], [6, 6], [6, 0], [0, 6]]
    check_basin(
        contour=contour,
        map_contour=[[0, 0], [0, 6], [6, 6], [6, 0]],
        ref_body=geometry.Polygon(contour),
        ref_shoreline_segments=[
            geometry.LineString([[0, 0], [3, 3]]),
            geometry.LineString([[6, 6], [3, 3]]),
            geometry.LineString([[6, 0], [3, 3]]),
            geometry.LineString([[0, 6], [3, 3]]),
        ],
        ref_closed=False,
    )


# - + + +
# + + + +
# + + + +
# + + + -
def test_adjoining_basin_few_times():
    contour = [[0, 2], [2, 2], [2, 0], [6, 0], [6, 4], [4, 4], [4, 6], [0, 6]]
    check_basin(
        contour=contour,
        map_contour=[[0, 0], [0, 6], [6, 6], [6, 0]],
        ref_body=geometry.Polygon(contour),
        ref_shoreline_segments=[
            geometry.LineString([[0, 2], [2, 2], [2, 0]]),
            geometry.LineString([[6, 4], [4, 4], [4, 6]]),
        ],
        ref_closed=False,
    )


# test input is the same map as for previous tests with georeferencinging as on
# plot below; band count is 1: 0 - not a basin, 1 - basin
#
#     0 2 4 6
#    _________
#   0|* * * *|
#   2|* * * *|
#   4|* * * *|
#   6|* * * *|
#    ---------


class FinderChecker(object):
    def __init__(self, data):
        self.__mockmap = MockMap(data)
        self.__finder = BasinsFinder(map=self.__mockmap, approx_error=0.1)

    def check_basins_count(self, ref_count):
        assert len(self.__finder.basins) == ref_count

    def check_basin(self, ref_basin_contour, basin_coo):
        basin = self.__finder.get_basin(basin_coo)
        ref_basin = Basin(
            contour=ref_basin_contour,
            map_contour=self.__mockmap.contour,
        )
        assert basin == ref_basin


# - - - -
# - + + -
# - + + -
# - - - -
def test_single_square_basin():
    checker = FinderChecker(
        [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]
    )
    checker.check_basins_count(1)
    checker.check_basin(
        ref_basin_contour=[
            [2.0, 2.0],
            [4.0, 2.0],
            [4.0, 4.0],
            [2.0, 4.0],
        ],
        basin_coo=Coordinate(3.0, 3.0, "EPSG:3857"),
    )


# - - - -
# + + + -
# - + + -
# - - + -
def test_single_triangle_basin():
    checker = FinderChecker(
        [[0, 0, 0, 0], [1, 1, 1, 0], [0, 1, 1, 0], [0, 0, 1, 0]]
    )
    checker.check_basins_count(1)
    checker.check_basin(
        ref_basin_contour=[[0.0, 2.0], [4.0, 2.0], [4.0, 6.0]],
        basin_coo=Coordinate(3.0, 3.0, "EPSG:3857"),
    )


# + + + -
# + + - -
# + - - -
# - - - -
def test_clipped_basin():
    checker = FinderChecker(
        [[1, 1, 1, 0], [1, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]]
    )
    checker.check_basins_count(1)
    checker.check_basin(
        ref_basin_contour=[[0, 0], [0.0, 4.0], [4.0, 0.0]],
        basin_coo=Coordinate(1.0, 1.0, "EPSG:3857"),
    )


# - - - -
# - - - -
# - - - -
# - - - -
def test_no_basin():
    checker = FinderChecker(
        [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    )
    checker.check_basins_count(0)


# - - - -
# - + + -
# - - - -
# - - - -
def test_small_basin():
    checker = FinderChecker(
        [[0, 0, 0, 0], [0, 1, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    )
    checker.check_basins_count(0)


# + + + +
# + + + +
# + + + +
# + + + +
def test_all_is_basin():
    checker = FinderChecker(
        [[1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]]
    )
    checker.check_basins_count(0)


# - - + +
# - - - +
# + - - -
# + + - -
def test_multiple_basins():
    checker = FinderChecker(
        [[0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 0], [1, 1, 0, 0]]
    )
    checker.check_basins_count(2)
    checker.check_basin(
        ref_basin_contour=[[4.0, 0.0], [6.0, 0.0], [6.0, 2.0]],
        basin_coo=Coordinate(5.5, 0.5, "EPSG:3857"),
    )
    checker.check_basin(
        ref_basin_contour=[[0.0, 4.0], [0.0, 6.0], [2.0, 6.0]],
        basin_coo=Coordinate(0.5, 5.5, "EPSG:3857"),
    )
