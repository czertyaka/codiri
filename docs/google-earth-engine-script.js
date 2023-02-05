var dataset = ee.ImageCollection("GLCF/GLS_WATER");
var water = dataset.select('water').median();

var lon = 0 // enter longitude
var lat = 0 // enter latitude
var radius = 0 // enter radius of area of interest
var region = ee.Geometry.Point(lat, lon).buffer(radius).bounds()

water = water.clip(region)
var waterVis = {
  min: 1,
  max: 2,
  palette: ['FAFAFA', '00C5FF']
};

Map.addLayer(water, waterVis, 'Water')
Export.image.toDrive({
  image: water,
  description: 'water',
  scale: 50,
  region: region,
  crs: 'EPSG:3857'
});
