from ..src.geo import distance, Coordinate, Map
import pytest
import numpy as np
import rasterio
import os


class TestCoordinate(object):
    def test_transform_to_3857(self):
        coo = Coordinate(lon=8.55, lat=47.36, crs="EPSG:4326")
        coo.transform("EPSG:3857")
        assert coo.lon == pytest.approx(955333.87, 0.1)
        assert coo.lat == pytest.approx(5272091.08, 0.1)
        assert coo.crs == "EPSG:3857"

    def test_transform_to_4326(self):
        coo = Coordinate(lon=955333.87, lat=5272091.08, crs="EPSG:3857")
        coo.transform("EPSG:4326")
        assert coo.lon == pytest.approx(8.55, 0.1)
        assert coo.lat == pytest.approx(47.36, 0.1)
        assert coo.crs == "EPSG:4326"


def test_distance():
    crs = "EPSG:3857"
    assert distance(
        Coordinate(1000, 1000, crs), Coordinate(1500, 1000, crs)
    ) == pytest.approx(500, 0.1)
    assert distance(
        Coordinate(1000, 1000, crs), Coordinate(1000, 1500, crs)
    ) == pytest.approx(500, 0.1)


class TestMap(object):
    def test_real_map(self):
        mymap = Map("../data/water.tif")
        assert mymap.data.dtype == "uint8"
        unique_array = np.unique(mymap.data)
        assert unique_array.size == 2
        assert unique_array[0] == 0
        assert unique_array[1] == 255

    def test_simple_map(self):
        data = np.array([[1, 2], [3, 4]]).astype("uint8")
        dataset = rasterio.open(
            "simple.tif",
            "w",
            driver="GTiff",
            height=2,
            width=2,
            dtype="uint8",
            crs="EPSG:3857",
            transform=[50, 0, 100, 0, -50, 100],
            count=1,
        )
        dataset.write(data, 1)
        dataset.close()

        mymap = Map("simple.tif")
        assert mymap.data[0][0] == 0
        assert mymap.data[0][1] == 255
        assert mymap.data[1][0] == 0
        assert mymap.data[1][1] == 0

        os.remove("simple.tif")
