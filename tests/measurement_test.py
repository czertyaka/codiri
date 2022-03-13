from codri.src.measurement import Measurement, SoilActivity
from codri.src.geo import Coordinate
import pytest


def test_soil_activity():
    specific_activity = 10
    activity = SoilActivity(specific_activity)
    assert activity.specific == specific_activity
    assert activity.surface_1cm == pytest.approx(140)


def test_measurement():
    measurement = Measurement(
        activity=0, coo=Coordinate(lon=10, lat=10, crs="EPSG:4326")
    )
    assert measurement.coo.crs == "EPSG:3857"
