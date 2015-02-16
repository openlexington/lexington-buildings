MAKEFLAGS+="-j 2" # chunking is slow, do this in parallel jobs

all: addresses BuildingOutlines2012 censustracts directories chunk_addrs chunk_bldgs osm

addresses.zip:
	curl -L "ftp://ftp.lojic.org/pub/federal/Address%20Sites.zip" -o addresses.zip

addresses: addresses.zip
	rm -rf addresses
	unzip addresses.zip -d addresses
	ogr2ogr -t_srs EPSG:4326 -overwrite addresses/addresses.shp addresses/Address\ Sites.shp

censustracts.zip:
	curl -L "http://api.censusreporter.org/1.0/data/download/latest?table_ids=B01001&geo_ids=140|05000US21111&format=shp" -o censustracts.zip

censustracts: censustracts.zip
	rm -rf censustracts
	unzip censustracts.zip -d censustracts
	ogr2ogr -t_srs EPSG:4326 -overwrite censustracts/tracts.shp censustracts/acs2013_5yr_B01001_14000US21111011102/acs2013_5yr_B01001_14000US21111011102.shp

BuildingOutlines2012.zip:
	curl -L "http://api.louisvilleky.gov/api/File/DownloadFile?fileName=Buildings_Shapefile.zip" -o BuildingOutlines2012.zip

BuildingOutlines2012: BuildingOutlines2012.zip
	rm -rf BuildingOutlines2012
	unzip BuildingOutlines2012.zip -d BuildingOutlines2012
	ogr2ogr -t_srs EPSG:4326 -overwrite BuildingOutlines2012/buildings4326.shp BuildingOutlines2012/Buildings.shp

chunks: directories
	rm -f chunks/*
	chunk_addrs
	chunk_bldgs

chunk_addrs: directories addresses censustracts
	python chunk.py addresses/addresses.shp censustracts/tracts.shp chunks/addresses-%s.shp geoid

chunk_bldgs: directories BuildingOutlines2012 censustracts
	python chunk.py BuildingOutlines2012/buildings4326.shp censustracts/tracts.shp chunks/buildings-%s.shp geoid

osm: directories chunk_addrs chunk_bldgs
	rm -f osm/*
#	python convert.py

directories:
	mkdir -p chunks
	mkdir -p osm
