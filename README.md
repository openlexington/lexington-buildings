Scripts for import of New Orleans address and building data.

## Prerequisites

Python modules needed include:
* fiona
* shapely

On Linux (Debian/Ubuntu) you should make sure the following packages are installed first:
* curl
* gdal-bin
* libgdal-dev
* python-dev
* python-pip
* python-shapely
* libspatialindex-dev

Then you can build/install fiona with:
    sudo pip install fiona

## Credits

Based on [dcbuildings](https://github.com/osmlab/dcbuildings) and [nycbuildings](https://github.com/osmlab/nycbuildings).

Adapted for New Orleans by Matt Toups.
