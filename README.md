Scripts for import of New Orleans address and building data.

To use, run:

    make

And if everything works you should get output in the `osm/` directory.

## Note

You don't need to be able to run this to participate in the import. This is available for those who are curious or would like to improve the process.

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

## More info

See https://wiki.openstreetmap.org/wiki/New_Orleans,_Louisiana/Building_Outlines_Import

Tracking the progress of this import at: http://tasks.openstreetmap.us/job/32
