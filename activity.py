#!/usr/bin/python3

from map import Map, transform_coo


def _log(msg):
    print("activity: " + msg)


class Cell(object):
    """Presents primitive cell on activity map"""

    def __init__(self, top, bottom, right, left):
        self.__top = top
        self.__bottom = bottom
        self.__right = right
        self.__left = left
        self.__activity = 0

    def set(self, activity):
        self.__activity = activity

    @property
    def top(self):
        return self.__top

    @property
    def bottom(self):
        return self.__bottom

    @property
    def right(self):
        return self.__right

    @property
    def left(self):
        return self.__left


class Measurment(object):
    """Holds info on activity measurement"""

    def __init__(self, activity, coo, crs="EPSG:4326"):
        """[specific activity] = Bq/kg"""
        self.__activity = activity
        coo = transform_coo(coo, crs)
        self.__coo = coo

    @property
    def activity(self):
        return self.__activity

    @property
    def coo(self):
        return self.__coo


class ActivityMap(object):
    """Holds discretizated activity distribution"""

    def __init__(self, geomap, x_cells=100, y_cells=100):
        self.__map = geomap
        self.__shorelines = dict()
        self.__init_cells(x_cells, y_cells)

    def add_shoreline(self, name, contour, width=2, act_depth=5):
        """[width] = m, [activity depth] = cm"""
        if width > self.__y_step or width > self.__x_step:
            raise Exception(
                f"shoreline width exceeds cell size: width = "
                f"{width}, cell height = {self.__y_step}, cell "
                f"width = {self.__x_step}"
            )
        self.__shorelines[name] = {
            "contour": contour,
            "width": width,
            "act_depth": act_depth,
            "measurements": [],
        }
        _log(f"adding shoreline '{name}'")

    def add_measurment(self, shoreline_name, measurment):
        if shoreline_name not in self.__shorelines:
            _log(f"shoreline named {shoreline_name} doesn't exists")
            return False
        _log(
            f"for shoreline {shoreline_name} added measurement: activity = "
            f"{measurment.activity} Bq/kg, coo = {measurment.coo}"
        )
        return True

    def calculate(self):
        pass

    def __init_cells(self, x_cells, y_cells):
        y_step = (
            self.__map.img.bounds.top - self.__map.img.bounds.bottom
        ) / y_cells
        self.__y_step = y_step
        x_step = (
            self.__map.img.bounds.right - self.__map.img.bounds.left
        ) / x_cells
        self.__x_step = x_step
        _log(
            f"intalizing activity map: cell width = {x_step} m, cell height ="
            f" {y_step} m"
        )
        self.__cells = []
        for j in range(y_cells):
            row = []
            left = self.__map.img.bounds.left + j * x_step
            right = left + x_step
            for i in range(x_cells):
                bottom = self.__map.img.bounds.bottom + i * y_step
                top = bottom + y_step
                row.append(Cell(top, bottom, right, left))
            self.__cells.append(row)


if __name__ == "__main__":
    map = Map(r"water.tif")
    activities = ActivityMap(map)
    activities.add_shoreline("B11-I", [])
    activities.add_measurment(
        "B11-I", Measurment(0, {"lon": 60.96793, "lat": 55.71958})
    )
    activities.add_measurment(
        "B12-I", Measurment(0, {"lon": 60.96793, "lat": 55.71958})
    )
