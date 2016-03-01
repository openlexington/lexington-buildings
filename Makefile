# MAKEFLAGS+="-j 2" # chunking is slow, do this in parallel jobs

all: addresses BuildingOutlines2007 blockgroups directories chunk_addrs chunk_bldgs osm

addresses: AddressPoint.zip
	rm -rf addresses
	unzip AddressPoint.zip -d addresses

blockgroups: lex-census-blockgroups.zip
	rm -rf blockgroups
	unzip lex-census-blockgroups.zip -d blockgroups

BuildingOutlines2007: lex-bldg-2007.zip
	rm -rf BuildingOutlines2007
	unzip lex-bldg-2007.zip -d BuildingOutlines2007

chunks: directories
	rm -f chunks/*
	chunk_addrs
	chunk_bldgs

chunk_addrs: directories addresses blockgroups
	python chunk.py addresses/AddressPoint.shp blockgroups/lex-census-blockgroups.shp chunks/AddressPoint-%s.shp geoid

chunk_bldgs: directories BuildingOutlines2007 blockgroups
	python chunk.py BuildingOutlines2007/lex-bldg-2007.shp blockgroups/lex-census-blockgroups.shp chunks/buildings-%s.shp geoid

osm: directories chunk_addrs chunk_bldgs
	rm -f osm/*
	python convert.py

directories:
	mkdir -p chunks
	mkdir -p osm
