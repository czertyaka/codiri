from bottom_deposits_radiocontamination.src.basins import (
    BasinsFinder,
    Basin,
)
from bottom_deposits_radiocontamination.src.geo import Coordinate
from bottom_deposits_radiocontamination.tests.mock import MockMap
import pytest
from shapely import geometry


# test input is small map 4x4 pix map
#
#     0 2 4 6
#    _________
#   0|* * * *|
#   2|* * * *|
#   4|* * * *|
#   6|* * * *|
#    ---------


def check_basin(basin_points, map_points, ref_contour, ref_shoreline_contour):
    basin = Basin(
        contour=basin_points,
        map_contour=map_points,
    )
    assert basin.contour == ref_contour
    assert basin.shoreline_contour == ref_shoreline_contour


# - - - -
# - + + -
# - + + -
# - - - -
def test_inner_basin():
    basin = geometry.LinearRing([[2, 2], [2, 4], [4, 4], [4, 2]])
    check_basin(
        basin_points=basin.coords[:-1],
        map_points=[[0, 0], [0, 6], [6, 6], [6, 0]],
        ref_contour=basin,
        ref_shoreline_contour=basin,
    )


# - - - -
# + + + -
# - + + -
# - - + -
def test_touching_basin():
    basin = geometry.LinearRing([[0, 2], [4, 2], [4, 6]])
    check_basin(
        basin_points=basin.coords[:-1],
        map_points=[[0, 0], [0, 6], [6, 6], [6, 0]],
        ref_contour=basin,
        ref_shoreline_contour=basin,
    )


# + + + -
# + + - -
# + - - -
# - - - -
def test_adjoining_basin():
    basin = geometry.LinearRing([[0, 0], [0, 4], [4, 0]])
    check_basin(
        basin_points=basin.coords[:-1],
        map_points=[[0, 0], [0, 6], [6, 6], [6, 0]],
        ref_contour=basin,
        ref_shoreline_contour=geometry.LineString([[0, 4], [4, 0]]),
    )


# + + + +
# + + + +
# + + + +
# + + + +
def test_filling_basin():
    map_cnt = geometry.LinearRing([[0, 0], [0, 6], [6, 6], [6, 0]])
    with pytest.raises(ValueError):
        Basin(contour=map_cnt, map_contour=map_cnt)


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
            contour=geometry.LinearRing(ref_basin_contour),
            map_contour=geometry.LinearRing(self.__mockmap.contour),
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
