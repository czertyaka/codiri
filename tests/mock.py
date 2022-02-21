from rasterio import Affine, MemoryFile
from numpy import array


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

    @property
    def contour(self):
        left, top = self.img.xy(0, 0, offset="ul")
        right, bottom = self.img.xy(
            self.img.width - 1, self.img.height - 1, offset="ul"
        )
        return [[left, top], [left, bottom], [right, bottom], [right, top]]
