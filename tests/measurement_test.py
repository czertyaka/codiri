from codri.src.measurement import Measurement
from codri.src.geo import Coordinate


def test_measurement():
    measurement = Measurement(
        activity=0, coo=Coordinate(lon=10, lat=10, crs="EPSG:4326")
    )
    assert measurement.coo.crs == "EPSG:3857"
