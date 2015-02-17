# OSM Import of Louisville, KY address and building data.

These scripts pre-process shapefile data from [data.louisvilleky.gov](https://data.louisvilleky.gov) and put it into a format suitable to be imported into OpenStreetMap.

To use, run:

    make

And if everything works you should get output in the `osm/` directory.

## Note

You don't need to be able to run this to participate in the import. This is available for those who are curious or would like to improve the process.

## Update

Updates to the addresses file on data.nola.gov January 2015 removed the ADDR\_TYPE field from the shapefile. This causes convert.py to fail, and we depend on ADDR\_TYPE to solve cases where two address points are in the exact same location.


## Prerequisites

You will need at least a few GB of RAM for this to work well. We also attempt to do work in parallel, so more CPU cores will be helpful.

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

Adapted for New Orleans by Matt Toups.  Adpated for Louisville, KY by Michael Schnuerle and Ate Poorthuis.

## More info

See http://wiki.openstreetmap.org/wiki/Louisville,_Kentucky/Building_Outlines_Import

Track the progress of this import at: http://tasks.openstreetmap.us/job/48
