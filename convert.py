# Convert DC building footprints and addresses into importable OSM files.
from fiona import collection
from lxml import etree
from lxml.etree import tostring
from rtree import index
from shapely.geometry import asShape, Point, LineString
from shapely import speedups
from sys import argv
from glob import glob
import re
from pprint import pprint
from decimal import Decimal, getcontext
from multiprocessing import Pool
import expansions # for streets etc
import os.path

getcontext().prec = 16

# Converts given building and address shapefiles into corresponding OSM XML
# files.
def convert(buildingIn, addressIn, osmOut):
    # Load all addresses.
    addresses = []
    with collection(addressIn, "r") as input:
        for address in input:
            shape = asShape(address['geometry'])
            shape.original = address
            addresses.append(shape)

    # Load and index all buildings.
    buildingIdx = index.Index()
    buildings = []
    with collection(buildingIn, "r") as input:
        for building in input:
            building['shape'] = asShape(building['geometry'])
            building['properties']['addresses'] = []
            buildings.append(building)
            buildingIdx.add(len(buildings) - 1, building['shape'].bounds)

    # Map addresses to buildings.
    for address in addresses:
        for i in buildingIdx.intersection(address.bounds):
            # unfortunately the address data is somewhat inaccurate, so sometimes the point falls
            # outside of the corresponding building. buffer() gives us a bit of wiggle room.
            # this is less than one meter, but fixes a lot of cases in the NOLA shapefile
            if address.buffer(0.000006).intersects(buildings[i]['shape']):
                buildings[i]['properties']['addresses'].append(address.original)

    # Generates a new osm id.
    osmIds = dict(node = -1, way = -1, rel = -1)
    def newOsmId(type):
        osmIds[type] = osmIds[type] - 1
        return osmIds[type]

    # Converts an address
    def convertAddress(address):
        result = dict()
        def direction(d):
            directions = dict()
            directions['N'] = 'North '
            directions['E'] = 'East '
            directions['S'] = 'South '
            directions['W'] = 'West '
            if d in directions:
                return directions[d]
            else:
                return ''

        def streettype(t):
            if t in expansions.road_types:
                return expansions.road_types[t]
            else:
                return t

        if all (k in address for k in ('HOUSENO', 'APT', 'STRNAME', 'TYPE', 'DIR' )):
            result['addr:housenumber'] = str(address['HOUSENO'])
            if address['APT']: # alpha-suffix to address
                result['addr:unit'] = str(address['APT'])
            if re.match('^(\d+)\w\w$', address['STRNAME']): # Test for 2ND, 14TH, 21ST
                streetname = address['STRNAME'].lower()
            else:
                if address['STRNAME']: # check if it exists
                    streetname = address['STRNAME'].title()
                else:
                    return result
            if address['TYPE']: # again check for existence
                result['addr:street'] = "%s%s %s" % \
                    (direction(address['DIR']),
                    streetname,
                    streettype(address['TYPE']) )
            else: # small number of streets have no type
                result['addr:street'] = "%s%s" % (direction(address['DIR']), streetname)
            if address['ZIPCODE']:
                result['addr:postcode'] = str(int(address['ZIPCODE']))
        return result

    # Appends new node or returns existing if exists.
    nodes = {}
    def appendNewNode(coords, osmXml):
        rlon = int(float(coords[0]*10**7))
        rlat = int(float(coords[1]*10**7))
        if (rlon, rlat) in nodes:
            return nodes[(rlon, rlat)]
        node = etree.Element('node', visible = 'true', id = str(newOsmId('node')))
        node.set('lon', str(Decimal(coords[0])*Decimal(1)))
        node.set('lat', str(Decimal(coords[1])*Decimal(1)))
        nodes[(rlon, rlat)] = node
        osmXml.append(node)
        return node

    def appendNewWay(coords, intersects, osmXml):
        way = etree.Element('way', visible='true', id=str(newOsmId('way')))
        firstNid = 0
        for i, coord in enumerate(coords):
            if i == 0: continue # the first and last coordinate are the same
            node = appendNewNode(coord, osmXml)
            if i == 1: firstNid = node.get('id')
            way.append(etree.Element('nd', ref=node.get('id')))
            
            # Check each way segment for intersecting nodes
            int_nodes = {}
            try:
                line = LineString([coord, coords[i+1]])
            except IndexError:
                line = LineString([coord, coords[1]])
            for idx, c in enumerate(intersects):
                if line.buffer(0.0000015).contains(Point(c[0], c[1])) and c not in coords:
                    t_node = appendNewNode(c, osmXml)
                    for n in way.iter('nd'):
                        if n.get('ref') == t_node.get('id'):
                            break
                    else:
                        int_nodes[t_node.get('id')] = Point(c).distance(Point(coord))
            for n in sorted(int_nodes, key=lambda key: int_nodes[key]): # add intersecting nodes in order
                way.append(etree.Element('nd', ref=n))
            
        way.append(etree.Element('nd', ref=firstNid)) # close way
        osmXml.append(way)
        return way

    # Appends an address to a given node or way.
    def appendAddress(address, element):
        for k, v in convertAddress(address['properties']).iteritems():
            element.append(etree.Element('tag', k=k, v=v))

    # Appends a building to a given OSM xml document.
    def appendBuilding(building, address, osmXml):
        # Check for intersecting buildings
        intersects = []
        try:
            for i in buildingIdx.intersection(building['shape'].bounds):
                for c in buildings[i]['shape'].exterior.coords:
                    if Point(c[0], c[1]).intersects(building['shape']):
                        intersects.append(c)
            # Export building, create multipolygon if there are interior shapes.
            way = appendNewWay(list(building['shape'].exterior.coords), intersects, osmXml)
            interiors = []
            for interior in building['shape'].interiors:
                interiors.append(appendNewWay(list(interior.coords), [], osmXml))
            if len(interiors) > 0:
                relation = etree.Element('relation', visible='true', id=str(newOsmId('way')))
                relation.append(etree.Element('member', type='way', role='outer', ref=way.get('id')))
                for interior in interiors:
                    relation.append(etree.Element('member', type='way', role='inner', ref=interior.get('id')))
                relation.append(etree.Element('tag', k='type', v='multipolygon'))
                osmXml.append(relation)
                way = relation
            way.append(etree.Element('tag', k='building', v='yes'))
    # lojic:bgnum tag for building identifier
            if 'BG_NUM' in building['properties']:
                way.append(etree.Element('tag', k='lojic:bgnum', v=str(int(building['properties']['BG_NUM']))))
##            bg_elev is rooftop elevation in feet, not building height
#            if 'BG_ELEV' in building['properties']:
#                height = round(((building['properties']['BG_ELEV'] * 12) * 0.0254), 1)
#                if height > 0:
#                    way.append(etree.Element('tag', k='height', v=str(height)))
            if address: appendAddress(address, way)
        # a few buildings have messy polygons
        except AttributeError as e:
            print "An attribute error in " + osmOut


    # Export buildings & addresses. Only export address with building if there is exactly
    # one address per building. Export remaining addresses as individual nodes.
    addresses = []
    osmXml = etree.Element('osm', version='0.6', generator='mtoups')
    for building in buildings:
        address = None
        if len(building['properties']['addresses']) == 1:
            address = building['properties']['addresses'][0] # simple case, only one address
        else: # there are more addresses. check to see if they're in the same location.
            if len(building['properties']['addresses']) > 1:
                seen = set()
                keepers = []
                for a in building['properties']['addresses']:
                    rounded_a = a['geometry']['coordinates'][0] , a['geometry']['coordinates'][1]
                    seen.add( rounded_a )
                    keepers.append(a)
                    # data.nola.gov has noise, round off to 7 decimal places (good enough for JOSM)
                    #if rounded_a in seen:
                        #lojic datta has not primary address property
#                        if a['properties']['ADDR_TYPE'] == 'P':
#                            keepers[0] = a # give priority to the primary address
#                    else: # another point within the building, but not the same exact coords
                        
                if len(keepers) == 1: # after filtering out dupes, are we down to 1 address?
                    address = keepers[0]
                else: # if there are multiple points in seperate locations, then we want individual nodes
                    addresses.extend(keepers)
        appendBuilding(building, address, osmXml)
    if (len(addresses) > 0):
        for address in addresses:
            node = appendNewNode(address['geometry']['coordinates'], osmXml)
            appendAddress(address, node)
    with open(osmOut, 'w') as outFile:
        outFile.writelines(tostring(osmXml, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
        print "Exported " + osmOut

def convertTown(buildingFile):
    matches = re.match('^.*-(.*)\.shp$', buildingFile).groups(0) # precincts may or may not contain letters
    osmPath = 'osm/buildings-addresses-%s.osm' % (matches[0])
    #print os.path.exists(osmPath)
    if os.path.exists(osmPath) == False:
        print "doing file " + 'osm/buildings-addresses-%s.osm' % (matches[0])
        convert(
            buildingFile,
            'chunks/addresses-%s.shp' % (matches[0]),
            'osm/buildings-addresses-%s.osm' % (matches[0]))


if __name__ == '__main__':
# Run conversions. Expects an chunks/addresses-[tract id].shp for each
# chunks/buildings-[tract id].shp. Optinally convert only one census tract.
    if (len(argv) == 2):
        convert(
            'chunks/buildings-%s.shp' % argv[1],
            'chunks/addresses-%s.shp' % argv[1],
            'osm/buildings-addresses-%s.osm' % argv[1])
    else:
        buildingFiles = glob("chunks/buildings-*.shp")

        pool = Pool()
        pool.map(convertTown, buildingFiles)
        pool.close()
        pool.join()
