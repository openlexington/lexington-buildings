MAKEFLAGS+="-j 2" # chunking is slow, do this in parallel jobs

all: NOLA_Addresses_20140221 BuildingOutlines2013 New_Orleans_Voting_Precincts directories chunk_addrs chunk_bldgs osm

NOLA_Addresses_20140221.zip:
	curl -L "https://data.nola.gov/download/div8-5v7i/application/zip" -o NOLA_Addresses_20140221.zip

NOLA_Addresses_20140221: NOLA_Addresses_20140221.zip
	rm -rf NOLA_Addresses_20140221
	unzip NOLA_Addresses_20140221.zip -d NOLA_Addresses_20140221
	ogr2ogr -t_srs EPSG:4326 -overwrite NOLA_Addresses_20140221/addresses.shp NOLA_Addresses_20140221/NOLA_Addresses_20140221.shp

New_Orleans_Voting_Precincts.zip:
	curl -L "https://data.nola.gov/api/geospatial/vycb-i8x3?method=export&format=Shapefile" -o New_Orleans_Voting_Precincts.zip

New_Orleans_Voting_Precincts: New_Orleans_Voting_Precincts.zip
	rm -rf New_Orleans_Voting_Precincts
	unzip New_Orleans_Voting_Precincts.zip -d New_Orleans_Voting_Precincts
	ogr2ogr -t_srs EPSG:4326 -overwrite New_Orleans_Voting_Precincts/precincts.shp New_Orleans_Voting_Precincts/VotingPrecinct.shp

BuildingOutlines2013.zip:
	curl -L "https://data.nola.gov/download/t3vb-bbwe/application/zip" -o BuildingOutlines2013.zip

BuildingOutlines2013: BuildingOutlines2013.zip
	rm -rf BuildingOutlines2013
	unzip BuildingOutlines2013.zip -d BuildingOutlines2013
#	ogr2ogr -simplify 0.2 -t_srs EPSG:4326 -overwrite BuildingOutlines2013/buildings.shp BuildingOutlines2013/BuildingOutlines2013.shp
	ogr2ogr -t_srs EPSG:4326 -overwrite BuildingOutlines2013/buildings.shp BuildingOutlines2013/BuildingOutlines2013.shp

chunks: directories
	rm -f chunks/*
	chunk_addrs
	chunk_bldgs

chunk_addrs: directories
	python chunk.py NOLA_Addresses_20140221/addresses.shp New_Orleans_Voting_Precincts/precincts.shp chunks/addresses-%s.shp PRECINCTID

chunk_bldgs: directories
	python chunk.py BuildingOutlines2013/buildings.shp New_Orleans_Voting_Precincts/precincts.shp chunks/buildings-%s.shp PRECINCTID

osm: directories chunk_addrs chunk_bldgs
	rm -f osm/*
	python convert.py

directories:
	mkdir -p chunks
	mkdir -p osm
