# codiri

## Introduction

**COntaminated Derelict Incipient Radiation Impact** - just a project I run for my gf master's thesis. Basically it'll do following:
1. download raster data for required area
2. find basins and their coastlines with predefined accuracy
3. add some specific activity measurements bounded with derelict coastline
4. calcualate effective doses in point of interest at the disaster initial phase due to wind uplift and transport 

## Usage

### Preparations

At first, one needs to prepare few input binary files.

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
