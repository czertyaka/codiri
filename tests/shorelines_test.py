from bottom_deposits_radiocontamination.src.shorelines import (
    ShorelinesFinder,
    ShorelineContour,
)
from bottom_deposits_radiocontamination.src.geo import Coordinate
from bottom_deposits_radiocontamination.tests.mock import MockMap
import pytest


def check_invalid_shoreline_contour(points):
    with pytest.raises(ValueError):
        ShorelineContour(points=points)


def test_shoreline_contour_empty():
    check_invalid_shoreline_contour([[]])


def test_shoreline_contour_point():
    check_invalid_shoreline_contour([[0, 0]])


def test_shoreline_contour_line_segment():
    cnt = ShorelineContour([[0, 0], [1, 1]], closed=True)
    assert cnt.closed is False


# test input is small map 4x4 pix with georeferencinging as on plot below
# band count is 1: 0 - not a basin, 1 - basin
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
        mockmap = MockMap(data)
        self.__finder = ShorelinesFinder(map=mockmap, approx_error=0.1)

    def check_cnts_count(self, ref_count):
        assert len(self.__finder.contours) == ref_count

    def check_cnt(self, ref_cnt, cnt_coo):
        assert self.__finder.get_cnt(cnt_coo) == ref_cnt


# - - - -
# - + + -
# - + + -
# - - - -
def test_single_square_basin():
    checker = FinderChecker(
        [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]
    )
    checker.check_cnts_count(1)
    checker.check_cnt(
        ref_cnt=ShorelineContour(
            points=[
                [2.0, 2.0],
                [4.0, 2.0],
                [4.0, 4.0],
                [2.0, 4.0],
            ],
            closed=True,
        ),
        cnt_coo=Coordinate(3.0, 3.0, "EPSG:3857"),
    )


# - - - -
# + + + -
# - + + -
# - - + -
def test_single_triangle_basin():
    checker = FinderChecker(
        [[0, 0, 0, 0], [1, 1, 1, 0], [0, 1, 1, 0], [0, 0, 1, 0]]
    )
    checker.check_cnts_count(1)
    checker.check_cnt(
        ref_cnt=ShorelineContour(
            points=[[0.0, 2.0], [4.0, 2.0], [4.0, 6.0]],
            closed=True,
        ),
        cnt_coo=Coordinate(3.0, 3.0, "EPSG:3857"),
    )


# + + + -
# + + - -
# + - - -
# - - - -
def test_clipped_basin():
    checker = FinderChecker(
        [[1, 1, 1, 0], [1, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]]
    )
    checker.check_cnts_count(1)
    checker.check_cnt(
        ref_cnt=ShorelineContour(
            points=[[0.0, 4.0], [4.0, 0.0]],
            closed=False,
        ),
        cnt_coo=Coordinate(1.0, 1.0, "EPSG:3857"),
    )


# - - - -
# - - - -
# - - - -
# - - - -
def test_no_basin():
    checker = FinderChecker(
        [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    )
    checker.check_cnts_count(0)


# - - - -
# - + + -
# - - - -
# - - - -
def test_small_basin():
    checker = FinderChecker(
        [[0, 0, 0, 0], [0, 1, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    )
    checker.check_cnts_count(0)


# + + + +
# + + + +
# + + + +
# + + + +
def test_all_is_basin():
    checker = FinderChecker(
        [[1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1]]
    )
    checker.check_cnts_count(0)


# - - + +
# - - - +
# + - - -
# + + - -
def test_multiple_basins():
    checker = FinderChecker(
        [[0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 0], [1, 1, 0, 0]]
    )
    checker.check_cnts_count(2)
    checker.check_cnt(
        ref_cnt=ShorelineContour(
            points=[[4.0, 0.0], [6.0, 2.0]],
            closed=False,
        ),
        cnt_coo=Coordinate(6.0, 0.0, "EPSG:3857"),
    )
    checker.check_cnt(
        ref_cnt=ShorelineContour(
            points=[[0.0, 4.0], [2.0, 6.0]],
            closed=False,
        ),
        cnt_coo=Coordinate(0.0, 6.0, "EPSG:3857"),
    )
