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
