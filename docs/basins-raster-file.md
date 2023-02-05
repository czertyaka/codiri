# Basins raster file

It should be a GeoTIFF file covering all the basins you will calculate doses from.
Program will read its' first band to a 8-bit array.
Though it is not required for your image to be 8-bit, make sure that each value can be safely
converted to 8-bit integer.
In other words,
```python
import numpy, rasterio
dataset = rasterio.open('basins.tif')
data = numpy.uint8(dataset.read(1))
```
should work.

Program expects that pixels will contain 2 for water. No other constraints.
You could have 137 for land, 0 for ice and so on.
It means that everything else except water is considered to be firm land, even snow/ice, clouds,
clouds shadows and etc.

The easiest way to obtain such file is to use Google Earth Engine
[Code Editor](https://code.earthengine.google.com/).
Make sure you have access to it and learn some basics on how to use it and you're ready to go.
I provide
[this](google-earth-engine-script.js)
script to make your life easier.
It uses
[GLCF: Landsat Global Inland Water](https://developers.google.com/earth-engine/datasets/catalog/GLCF_GLS_WATER)
dataset (in case you were windering, why I use value of 2 to mark pixels with water, read this
dataset specification).
Modify variables `lon`, `lat` and `radius` for your needs and run code.
You'll get your very desired file on your Google Drive in no time.
