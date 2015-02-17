MAKEFLAGS+="-j 2" # chunking is slow, do this in parallel jobs

all: addresses BuildingOutlines2012 blockgroups directories chunk_addrs chunk_bldgs osm

addresses.zip:
	curl -L "ftp://ftp.lojic.org/pub/federal/Address%20Sites.zip" -o addresses.zip

addresses: addresses.zip
	rm -rf addresses
	unzip addresses.zip -d addresses
	ogr2ogr -t_srs EPSG:4326 -overwrite addresses/addresses.shp addresses/Address\ Sites.shp

blockgroups.zip:
	curl -L "http://api.censusreporter.org/1.0/data/download/latest?table_ids=B01001&geo_ids=150|05000US21111&format=shp" -o blockgroups.zip

blockgroups: blockgroups.zip
	rm -rf blockgroups
	unzip blockgroups.zip -d blockgroups
	ogr2ogr -t_srs EPSG:4326 -overwrite blockgroups/blockgroups.shp blockgroups/acs2013_5yr_B01001_15000US211110115132/acs2013_5yr_B01001_15000US211110115132.shp

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

chunk_addrs: directories addresses blockgroups
	python chunk.py addresses/addresses.shp blockgroups/blockgroups.shp chunks/addresses-%s.shp geoid

chunk_bldgs: directories BuildingOutlines2012 blockgroups
	python chunk.py BuildingOutlines2012/buildings4326.shp blockgroups/blockgroups.shp chunks/buildings-%s.shp geoid

osm: directories chunk_addrs chunk_bldgs
	rm -f osm/*
#	python convert.py

directories:
	mkdir -p chunks
	mkdir -p osm
