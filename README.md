# codiri

## Introduction

`codiri` stands for "COntaminated Derelict Incipient Radiation Impact".
Derangment of this name comes from its nature.
I now must warn you, stranger, this is not for common use.
Project deals with very specific problem in radiation safety.

Imagine industrial basin near nuclear facility that produces liquid radioactive waste
and utilizes this basin to store it.
There are certain summer days when sun is so close to these lands of mortals that, once exposed
to it, you seek shelter in haste.
The water these days does not bring comfort, on contrary, it becomes warm and nasty, you can even see
it evaporazing.
Talking about evaporation...
Water level drops down.
It is about several meters of coastline that was under water back then, but now it sees light.
So do radioactive wastes. It is to a certain extent safe unless you want to settle down near it for long.
But wind may take care of such unjustness.
It may carry wastes hidden in coastline soil up to your doorstep.
Double-trouble...

So, this code serves for effective dose calculation in such situation.
This envolves a lot of input data. I mean it. A lot.
One hardly will be able to use this code unless he/she is failry familiar with
calculation model which were taken from certain
[Russian security manual](https://github.com/czertyaka/codiri/wiki/Reference-Textbooks).

Then again, this is not your case if you wish to perform calculation according to other model.
But my ~~gf~~ wife along with her scientific advisor wants exactly that.
So I obey.

## Usage

### Requirements

It is, as usual, strongly recommended for you to use `Python` virtual environment or container
(for now, it is up to user to write `Dockerfile`).
Further code snippets assume that you chose to work in `venv`.

At first, activate virtual environment.
```bash
python3 -m venv venv
source venv/bin/activate
```

Since we will not return to `venv` anymore, here's how you exit virtual environment when you're done.
```bash
deactivate
```

Install required packages:
```bash
pip install -r <codiri path>/requirements.txt
```

### Testing

It's smart to run some sanity check before wasting a lot of time preparing input files.
You can use unit-tests for such purpose.
```bash
cd <codiri path>/tests
pytest .
```

You'll now if something went wrong.

### Preparations

Then, you need to prepare few input binary files.

* First one is geospatial raster file which will be used to form activity map, typically it has `.tif` extension.
It, of course, should cover area of interest, e.g. basins you need to calculate dose from.
Basically, each raster unit contains `0` for firm land and `255` for watery surface.
[Here]() you can find it's specification and ways to obtain it.
For our usage scenario let's assume it has name `water.tif`.

* Second one is database for reference values for computational model such as radiation decay coefficients,
age groups, dose coefficients and etc.
It may need to put some effort into preparing this one since computation model uses much more of reference values
than of user input.
It is expected to be database formed with [dataset](https://dataset.readthedocs.io/en/latest/#) `Python` package.
It's structure and ways of it's provisioning may be found [here]().
I will refer to the database as `reference.db` later.

It's unlikely that you'll need to modify these two very often.
But there are another file.
It contains all the values that can not be considered as reference
(meaning they are specific to you certain situation).
Since you will probably need to change one or two of them regularly they are stored in `json` file.
List of these variables, theirs units and hierarchy you may find [here]().
I'm not only extremely smart, but also very kind, so I provide this [template]().
Let's assume you gave it name `input.json`

### Calculation

So, I guess you already prepared calculation environment and it looks something like this:
```
$ tree -L
.
├── codiri
│   ├── calculate.py
│   ├── data
│   ├── __init__.py
│   ├── main.py
│   ├── plot.py
│   ├── __pycache__
│   ├── pyproject.toml
│   ├── README.md
│   ├── requirements.txt
│   ├── src
│   ├── tests
│   └── utils.py
├── data
│   ├── README.md
│   ├── reference_data.db
│   └── water.tif
├── input
│   └── input.json
└── venv
    ├── bin
    ├── include
    ├── lib
    ├── lib64 -> lib
    ├── pyvenv.cfg
    └── share

14 directories, 13 files
```

Run calculation like this:
```bash
python codiri/calculate.py -i inlut/input.json -o results
```
Output example:
```
report directory: results/report_04-02-2023_21-08-25
map: opened image '/home/czert/projects/codiri/data/water.tif'; bounds = BoundingBox(left=6771550.0, bottom=7480900.0, right=6806900.0, top=7516450.0), crs = EPSG:3857, width = 707 pix, height = 711 pix
shorelines: found 102 basins
shorelines: Douglas-Peucker approximation algorithm epsilon = 1%
shorelines: added 42 basins
Metlino; Cs-137: acute 1.30e-09; period 7.85e-08; Sr-90: acute 1.41e-11; period 1.86e-07
Hudaiberdinsky; Cs-137: acute 9.68e-10; period 7.82e-08; Sr-90: acute 8.61e-12; period 1.86e-07
Novogorny; Cs-137: acute 8.69e-10; period 7.81e-08; Sr-90: acute 7.08e-12; period 1.86e-07
Ibragimova; Cs-137: acute 7.93e-10; period 7.80e-08; Sr-90: acute 5.99e-12; period 1.86e-07
NovayaTecha; Cs-137: acute 8.53e-10; period 7.80e-08; Sr-90: acute 6.84e-12; period 1.86e-07
BolshoyKuyash; Cs-137: acute 7.84e-10; period 7.80e-08; Sr-90: acute 5.87e-12; period 1.86e-07
Tatysh; Cs-137: acute 6.89e-10; period 7.79e-08; Sr-90: acute 4.66e-12; period 1.86e-07
Kasli; Cs-137: acute 6.19e-10; period 7.78e-08; Sr-90: acute 3.88e-12; period 1.86e-07
Kyshtym; Cs-137: acute 5.62e-10; period 7.77e-08; Sr-90: acute 3.28e-12; period 1.86e-07
map: opened image '/home/czert/projects/codiri/data/water.tif'; bounds = BoundingBox(left=6771550.0, bottom=7480900.0, right=6806900.0, top=7516450.0), crs = EPSG:3857, width = 707 pix, height = 711 pix
shorelines: found 102 basins
shorelines: Douglas-Peucker approximation algorithm epsilon = 1%
shorelines: added 42 basins
plot: data/compass.png is missing
plot: data/compass.png is missing
plot: data/compass.png is missing
plot: results/report_04-02-2023_21-08-25/bin/coords.npy is missing
```
Directiry with results content:
```
$ tree results
results
└── report_04-02-2023_21-08-25
    ├── basins.png
    ├── bin
    │   ├── Cs-137_actmap.tif
    │   ├── raster_factors.json
    │   └── Sr-90_actmap.tif
    ├── Cs-137_actmap.png
    ├── input.json
    ├── special_points.csv
    └── Sr-90_actmap.png

3 directories, 8 files
```

Program generated report directory with unique name.
The output is bunch of plot images and text data.
The input file were also copied to report just for the record.
Here is brief explanation for each output file in root directory of report:
* `basins.png` is a picture of labeled contaminated basins over geographical coordinates;
* `<nuclide name>_actmap.png` is a heatmap of activity distribution on derelict coastline;
* `special_points.json` has amount of resulting and intermediate calculated values for
each point of interest, e.g. effective acute dose, effective dose for 1st year, depletions for
each atmospheric stability cathegory and so on.

The `bin` directory is not for user's use.
