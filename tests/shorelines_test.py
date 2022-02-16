from bottom_deposits_radiocontamination.src.shorelines import (
    ShorelinesFinder,
    ShorelineContour,
)
from bottom_deposits_radiocontamination.src.geo import Coordinate
from numpy import array
from rasterio import Affine, MemoryFile

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


class MockMap(object):
    """class for mocking ..src.geo.Map"""

    def __init__(self, data):
        data = array(data).astype("uint8")
        assert data.shape == (4, 4)

        memfile = MemoryFile()
        dataset = memfile.open(
            driver="GTiff",
            height=data.shape[0],
            width=data.shape[1],
            dtype="uint8",
            crs="EPSG:3857",
            transform=Affine.scale(2.0, 2.0),
            count=1,
        )
        dataset.write(data, 1)

        self.__data = data
        self.__img = dataset

    @property
    def img(self):
        return self.__img

    @property
    def data(self):
        return self.__data


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
