#!/usr/bin/env python3

import datetime
import math
import os
import random
import re
import string
import sys


OUTPUT_PREAMBLE = """
# You can easily add GPSs to your list by making an LCD, opening the text edit
# by hitting 'F', and pasting your desired GPSs into it.  Then go into your GPS
# list, and turn them on.
#
# Order of Precedence:
#   U (Uranium)
#   PT (Platnium)
#   AU (Gold)
#   AG (Silver)
#   ICE
#   MG (Magnesium)
#   CO (Cobalt)
#   NI (Nickel)
#   SI (Silicon)
#   FE (Iron)
""".strip()

# Coordinates from ingame "!nexus getsectors true". Remove the ':' character in
# the radius. Must be in priority order. GPS coordinate will be considered in
# the first sector in this list that matches.
#
# All inner zones must come before outer zones. For example Auroria Planet
# comes before Auroria Space. The Hub comes before Roach Motel. Zarion Space
# comes before Goldilocks Zone.
#
# This list is processed early in process_sectors(), converting each item into
# an item similar to the following:
# {
#     'coordinate': {
#         'name': 'Auroria Planet - (R250km)',
#         'x': -2894701.55,
#         'y': 1033798.5,
#         'z': 2003378.29,
#         'colour': '#FFFFFF00',
#         'notes': '',
#         'sector': 'AP'
#     },
#     'abbr': 'AP',
#     'header': 'Auroria Planet PvE',
#     'radius': 250000
# }
SECTORS = [
    {
        'coordinate': 'GPS:Auroria Planet - (R250km):' +
                      '-2894701.55:1033798.5:2003378.29:#FFFFFF00:',
        'abbr': 'AP',
        'header': 'Auroria Planet PvE'
    },
    {
        'coordinate': 'GPS:Auroria Space - (R750km):' +
                      '-2894701.55:1033798.5:2003378.29:#FFFFFF00:',
        'abbr': 'AS',
        'header': 'Auroria Space PvE'
    },
    {
        'coordinate': 'GPS:K.O.T.H - (R250km):' +
                      '5018866.7:-6120757.03:4566088.55:#FFFFFF00:',
        'abbr': 'KH',
        'header': 'K.O.T.H. PvP'
    },
    {
        'coordinate': 'GPS:Korrath Planet - (R600km):' +
                      '-917607.09:-232737.66:-9611492.83:#FFFFFF00:',
        'abbr': 'KP',
        'header': 'Korrath Planet PvP'
    },
    {
        'coordinate': 'GPS:Korrath Space - (R1000km):' +
                      '-917607.09:-232737.66:-9611492.83:#FFFFFF00:',
        'abbr': 'KS',
        'header': 'Korrath Space PvP'
    },
    {
        'coordinate': 'GPS:Paratha Prime Planet - (R250km):' +
                      '2210546.1:0:3529973.22:#FFFFFF00:',
        'abbr': 'PP',
        'header': 'Paratha Planet PvE'
    },
    {
        'coordinate': 'GPS:Paratha Prime Space - (R750km):' +
                      '2210546.1:0:3529973.22:#FFFFFF00:',
        'abbr': 'PS',
        'header': 'Paratha Space PvE'
    },
    {
        'coordinate': 'GPS:Ravarna Planet - (R250km):' +
                      '6892920.19:266488.22:-163203.33:#FFFFFF00:',
        'abbr': 'RP',
        'header': 'Ravarna Planet PvP'
    },
    {
        'coordinate': 'GPS:Ravarna Space - (R750km):' +
                      '6892920.19:266488.22:-163203.33:#FFFFFF00:',
        'abbr': 'RS',
        'header': 'Ravarna Space PvP'
    },
    {
        'coordinate': 'GPS:Umbra Planet - (R250km):' +
                      '1190569.51:-8672830.43:-1339138.72:#FFFFFF00:',
        'abbr': 'UP',
        'header': 'Umbra Planet Pv?'
    },
    {
        'coordinate': 'GPS:Umbra Space - (R750km):' +
                      '1190569.51:-8672830.43:-1339138.72:#FFFFFF00:',
        'abbr': 'US',
        'header': 'Umbra Space Pv?'
    },
    {
        'coordinate': 'GPS:Volcanis Planet - (R250km):' +
                      '-5311681.54:1664010.91:-3307980.03:#FFFFFF00:',
        'abbr': 'VP',
        'header': 'Volcanis Planet PvP'
    },
    {
        'coordinate': 'GPS:Volcanis Space - (R750km):' +
                      '-5311681.54:1664010.91:-3307980.03:#FFFFFF00:',
        'abbr': 'VS',
        'header': 'Volcanis Space PvP'
    },
    {
        'coordinate': 'GPS:Zarion Planet - (R250km):' +
                      '1088776.01:0:-2619759:#FFFFFF00:',
        'abbr': 'ZP',
        'header': 'Zarion Planet PvE'
    },
    {
        'coordinate': 'GPS:Zarion Space - (R750km):' +
                      '1088776.01:0:-2619759:#FFFFFF00:',
        'abbr': 'ZS',
        'header': 'Zarion Space PvE'
    },
    {
        'coordinate': 'GPS:The Hub - (R500km):0:0:0:#FFFFFF00:',
        'abbr': 'HB',
        'header': 'The Hub PvE'
    },
    {
        'coordinate': 'GPS:Roach Motel - (R1500km):0:0:0:#FFFFFF00:',
        'abbr': 'RM',
        'header': 'Roach Motel PvE'
    },
    {
        'coordinate': 'GPS:The Goldilocks Zone - (R5000km):0:0:0:#FFFFFF00:',
        'abbr': 'GZ',
        'header': 'Goldilocks Zone PvE'
    },
    {
        'coordinate': 'GPS:Roach Hostel - (R6000km):0:0:0:#FFFFFF00:',
        'abbr': 'RH',
        'header': 'Roach Hostel PvE'
    },
    {
        'coordinate': 'GPS:Contested Barrens - (R8500km):0:0:0:#FFFFFF00:',
        'abbr': 'CB',
        'header': 'Contested Barrens PvP'
    }
]

# Ore abbreviation, in priority order
ORES = [
    'U',
    'PT',
    'AU',
    'AG',
    'ICE',
    'MG',
    'CO',
    'NI',
    'SI',
    'FE'
]

CLUSTER_PREFIX = 'Cluster'

# 2km
DUPLICATE_RESOURCE_DISTANCE_METERS = 2 * 1000

# 500km
DUPLICATE_CLUSTER_DISTANCE_METERS = 500 * 1000


def main():
    """
    Read Space Engineers GPS coordinates from a file. Sort the coordinates into
    clusters.
    """

    if len(sys.argv) != 3:
        sys.stderr.write('Wrong number of arguments!\n')
        usage()
        exit(1)

    input_filename = sys.argv[1]
    output_filename = sys.argv[2]

    if not os.path.isfile(input_filename):
        sys.stderr.write(f'Input file does not exsit: {input_filename}\n')
        usage()
        exit(1)

    if os.path.exists(output_filename):
        sys.stderr.write(f'Output file already exists: {output_filename}\n')
        usage()
        exit(1)

    process_sectors()

    with open(input_filename) as handle:
        coordinates = read_coordinates_from_handle(handle)

    (clusters, resources) = sort_coordinates(coordinates)

    clusters = deduplicate_coordinates(
        clusters, DUPLICATE_CLUSTER_DISTANCE_METERS)
    resources = deduplicate_coordinates(
        resources, DUPLICATE_RESOURCE_DISTANCE_METERS)

    fix_names(resources)

    make_names_unique(resources)

    cluster_coordinates(clusters, resources)

    clusters.sort(
        key=lambda cluster: sector_index(cluster['sector']), reverse=True)

    current_sector_header = None

    with open(output_filename, 'w') as handle:
        current_date = datetime.datetime.today().strftime('%Y.%m.%d')
        handle.write(f"# Up-to-date as of {current_date}\n#\n")
        handle.write(f'{OUTPUT_PREAMBLE}\n\n')
        for cluster in clusters:

            # Print header if different than the last header
            for sector in SECTORS:
                if sector['abbr'] == cluster['sector']:
                    if sector['header'] != current_sector_header:
                        handle.write(f'\n# {sector["header"]}:\n\n')
                        current_sector_header = sector['header']

            if 'resources' in cluster:
                handle.write(f'{coordinate_to_se_gps(cluster)}\n')
                cluster['resources'].sort(
                    key=lambda coord: ORES.index(coord['name'].split()[1]))
                for resource in cluster['resources']:
                    handle.write(f'{coordinate_to_se_gps(resource)}\n')
                handle.write('\n')

    print(f'Coordinates output to {output_filename}')


def sector_index(sector_abbr):
    """
    Get the index of a sector.

    Parameters
    ----------
    sector_abbr : str
        The sector abbreviation.

    Returns
    -------
    int
        The index of the sector.
    """

    for i in range(len(SECTORS)):
        if SECTORS[i]['abbr'] == sector_abbr:
            return i

    return -1


def process_sectors():
    """
    Process sectors, converting the GPS string into a coordinate dict. Adds the
    radius.

    Raises
    ------
    Exception
        The sector coordinate name was not in the expected from.
    """

    for sector in SECTORS:
        coordinate = parse_coordinate(sector['coordinate'], sector['abbr'])
        sector['coordinate'] = coordinate

        radius_match = re.search(r'\(R(\d+)km\)', coordinate['name'])
        if radius_match is None:
            raise Exception(
                f"Unexpected sector GPS name: {coordinate['name']}")
        sector['radius'] = int(radius_match.group(1)) * 1000


def usage():
    """
    Print usage information to the screen.
    """

    print('Usage:')
    print('\t./se_gps.py <input_file> <output_file>')


def read_coordinates_from_handle(coordinate_input):
    """
    Reads the coordinates from the file handle, parse them, and return the list
    of parsed coordinates.

    Parameters
    ----------
    coordinate_input : TextIOWrapper
        The open file handle to read the coordinates from.

    Returns
    -------
    list
        The list of parsed coordinates.
    """

    coordinates = []
    for coordinate_line in coordinate_input:
        coordinate = parse_coordinate(coordinate_line)
        if coordinate is None:
            continue
        coordinates.append(coordinate)
    return coordinates


def parse_coordinate(coordinate_line, sector=None):
    """
    Parse a coordinate line, returning the coordinate dictionary.

    Parameters
    ----------
    coordinate_line : str
        The coordinate line.
    sector : str | None
        Optional. If not set the sector will be discovered from the sector
        list.

    Returns
    -------
    dict | None
        The parsed coordinate as a dict containing the following keys:

            name : str
            x : float
            y : float
            z : float
            sector : str
            colour : str
            notes : str

        If the coordinate could not be parsed an error is printed to stderr and
        None is returned.
    """

    coordinate_line = coordinate_line.strip()
    if len(coordinate_line) == 0:
        # Empty line, just skip
        return None

    if coordinate_line.startswith('#'):
        # Skip comments
        return None

    coordinate_tokens = coordinate_line.split(':')
    if len(coordinate_tokens) < 7:
        sys.stderr.write(
            f'Bad coordinate, wrong number of tokens: {coordinate_line}\n')
        return None

    coordinate = {
        'name': coordinate_tokens[1],
        'x': float(coordinate_tokens[2]),
        'y': float(coordinate_tokens[3]),
        'z': float(coordinate_tokens[4]),
        'colour': coordinate_tokens[5],
        'notes': coordinate_tokens[6]
    }

    if sector is None:
        sector = find_coordinate_sector(coordinate)
    coordinate['sector'] = sector

    return coordinate


def find_coordinate_sector(coordinate):
    """
    Get the sector the coordinate is in.

    Parameters
    ----------
    coordinate : dict
        The coordinate.

    Returns
    -------
    str
        The sector the coordinate is in.

    Raises
    ------
    Exception
        The coordinate was not in a sector.
    """

    for sector in SECTORS:
        distance = check_distance(sector['coordinate'], coordinate)
        if distance < sector['radius']:
            return sector['abbr']

    raise Exception(f'No sector fonud for coordinate: {str(coordinate)}')


def deduplicate_coordinates(coordinates, min_distance):
    """
    Remove duplicate coordinates from the coordinate list.

    Parameters
    ----------
    coordinates : list
        The list of coordinates.
    min_distance : int
        Distance in meters. Coordinates within this distance will be considered
        duplicates.

    Returns
    -------
    list
        The coordinates with duplicates removed.
    """

    for coordinate in coordinates:
        if is_duplicate(coordinate):
            continue
        duplicates = find_duplicates(coordinate, coordinates, min_distance)
        if len(duplicates) > 0:
            handle_duplicates(duplicates)

    deduped_coordinates = []
    for coordinate in coordinates:
        if not is_duplicate(coordinate):
            deduped_coordinates.append(coordinate)

    return deduped_coordinates


def find_duplicates(coordinate, coordinates, min_distance):
    """
    Find duplicates coordinates.

    Parameters
    ----------
    coordinate : dict
        The coordinate to test against.
    coordinates : list
        The list of coordinates.

    Returns
    -------
    list
        The list of tuples (dict, int). Each tuple contains a duplicate
        coordinate and the distance between the coordinates.
    """

    duplicates = []

    for test_coordinate in coordinates:
        if coordinate == test_coordinate:
            continue
        if is_duplicate(test_coordinate):
            continue
        if coordinate['sector'] != test_coordinate['sector']:
            continue
        distance = check_distance(coordinate, test_coordinate)
        if distance < min_distance:
            duplicates.append((test_coordinate, distance))

    if len(duplicates) > 0:
        duplicates.insert(0, (coordinate, 0))

    return duplicates


def check_distance(a, b):
    """
    Calculate the distance between two coordinates.

    Parameters
    ----------
    a : dict
        The first coordinate.
    b : dict
        The second coordinate.

    Returns
    -------
    int
        The distance between the coordinates in meters, rounded to the nearest
        meter.
    """

    return round(math.sqrt(
        (b['x'] - a['x']) ** 2 +
        (b['y'] - a['y']) ** 2 +
        (b['z'] - a['z']) ** 2))


def is_duplicate(coordinate):
    """
    Check if a coordinate has been marked as a duplicate coordinate.

    Parameters
    ----------
    coordinate : dict
        The coordinate to check if it's a duplicate.

    Returns
    -------
    bool
        True if the coordinate is a duplicate, False otherwise.
    """

    if 'duplicate' in coordinate:
        return coordinate['duplicate']
    return False


def handle_duplicates(duplicates):
    """
    Notify the user of the duplicate. Prompt the user to choose which one to
    mark as a duplicate.

    Parameters
    ----------
    duplicates : list
        List of tuples (dict, int). The coordinates, and distance to the first
        coordinate in the list that are duplicates.
    """

    print('Duplicate coordinates found!')
    print()
    index = 1
    for (coordinate, distance) in duplicates:
        print(f"\t{index}) {coordinate['name']} ({distance}m)")
        index += 1
    print()

    while True:
        try:
            response = int(input('Choose which coordinate to keep: ').strip())
            if response >= 1 and response <= index:
                mark_duplicates(duplicates, response - 1)
                break
        except Exception:
            # Fall through to the invalid response
            pass

        print('Invalid response.')

    print()


def mark_duplicates(duplicates, skip_index):
    """
    Mark all but one coordinates as duplicates.

    Parameters
    ----------
    duplicates : tuple (dist, int)
        The list of duplicates. The first element is the coordinate, the second
        element is the distance to the first duplicate coordinate.
    skip_index : int
        The index to skip. One coordinate will be kept and not marked as a
        duplicate. This is the index of that coordinate. Skip this coordinate,
        not marking it as a duplicate.
    """

    for i in range(len(duplicates)):
        if i == skip_index:
            continue
        (coordinate, _) = duplicates[i]
        coordinate['duplicate'] = True


def sort_coordinates(coordinates):
    """
    Sort coordinates into clusters and resources. If the name of a coordinate
    starts with CLUSTER_PREFIX then it's considered a cluster coordinate,
    otherwise it's considered a resource coordinate.

    Parameters
    ----------
    coordinates : list
        List of coordinates.

    Returns
    -------
    tuple (list, list)
        A tuple with two elements. The first element is the list of cluster
        coordinates, the second element is the list of resource coordinates.
    """

    clusters = []
    resources = []

    for coordinate in coordinates:
        if coordinate['name'].startswith(CLUSTER_PREFIX):
            clusters.append(coordinate)
        else:
            resources.append(coordinate)

    return (clusters, resources)


def cluster_coordinates(clusters, resources):
    """
    Group the resources. Resource coordinates are added to the cluster
    coordinates using a new dict key 'resources'.

    Parameters
    ----------
    clusters : list
        A list of dicts. The cluster coordinates. The resources key is added to
        each cluster. It contains a list of resources that is near the cluster.
    resources : list
        A list of dicts. The resource coordinates. The resources are added to
        the clusters based on distance.
    """

    new_clusters = []

    for cluster in clusters:
        # Add the cluster to its own group
        cluster['notes'] = sanitize_folder_name(cluster['name'])

    for resource in resources:
        (distance, cluster) = find_nearest_cluster(resource, clusters)
        if distance is None or distance > DUPLICATE_CLUSTER_DISTANCE_METERS:
            cluster = create_cluster_for_resource(resource)
            clusters.append(cluster)
            new_clusters.append(cluster)

        # Add the cluster to a folder
        resource['notes'] = cluster['notes']

        if 'resources' not in cluster:
            cluster['resources'] = []
        cluster['resources'].append(resource)

    # For the new clusters, reposition the cluster GPS to the center of the
    # cluster.
    for cluster in new_clusters:
        total_x = 0
        total_y = 0
        total_z = 0
        for resource in cluster['resources']:
            total_x += resource['x']
            total_y += resource['y']
            total_z += resource['z']
        total_resources = len(cluster['resources'])
        cluster['x'] = round(total_x / total_resources, 2)
        cluster['y'] = round(total_y / total_resources, 2)
        cluster['z'] = round(total_z / total_resources, 2)


def create_cluster_for_resource(resource):
    """
    Generate a random custer name at the same GPS coordinates as the provided
    coordinate.

    Parameters
    ----------
    resource : dict

    """

    random_name_postfix = ''.join(
        random.SystemRandom().choice(string.ascii_uppercase) for _ in range(4))
    name = f'{CLUSTER_PREFIX} {random_name_postfix}'

    cluster = {
        'name': name,
        'x': resource['x'],
        'y': resource['y'],
        'z': resource['z'],
        'colour': resource['colour'],
        'notes': sanitize_folder_name(name),
        'sector': resource['sector']
    }

    return cluster


def sanitize_folder_name(name):
    """
    Sanitize a GPS folder name.

    Parameters
    ----------
    name : str
        The name to sanitize.

    Returns
    -------
    str
        The sanitized GPS folder name.
    """

    name = name.replace(' ', '_')
    name = name.replace('(', '')
    name = name.replace(')', '')
    name = name.replace(',', '')

    return name


def find_nearest_cluster(resource, clusters):
    """
    Find the cluster nearest the resource.

    Parameters
    ----------
    resource : dict
        The resource coordinate.
    clusters : list
        The list of cluster coordinates

    Returns
    -------
    tuple (int | None, dict | None)
        A tuple with two elements. The first element is the distance to the
        nearest cluster in meters. The second element is the nearest cluster
        coordinate.

        If no cluster is in the same sector as the resource (None, None) is
        returned.
    """

    nearest_cluster = None
    nearest_cluster_distance = None
    for cluster in clusters:
        if cluster['sector'] != resource['sector']:
            continue
        distance = check_distance(resource, cluster)
        if (nearest_cluster_distance is None or
                distance < nearest_cluster_distance):
            nearest_cluster = cluster
            nearest_cluster_distance = distance

    return (nearest_cluster_distance, nearest_cluster)


def coordinate_to_se_gps(coordinate):
    """
    Convert a coordinate into a GPS string that can be imported into Space
    Engineers.

    Parameters
    ----------
    coordinate : dict
        The coordinate to convert into the GPS string.

    Returns
    -------
    str
        A GPS string that can be imported into Space Engineers.
    """

    name = coordinate['name']
    x = str(coordinate['x'])
    y = str(coordinate['y'])
    z = str(coordinate['z'])
    colour = coordinate['colour']
    notes = coordinate['notes']

    return f'GPS:{name}:{x}:{y}:{z}:{colour}:{notes}:'


def fix_names(resources):
    """
    Fix and normalize all resource names.

    Parameters
    ----------
    resources : list
        List of all resource coordinates.
    """

    for resource in resources:
        name = resource['name']
        sector = resource['sector']
        while (normalized_name := normalize_name(name, sector)) is None:
            print(f'Invalid name: {name}')
            name = input('Enter a new name: ').strip()
        resource['name'] = normalized_name


def normalize_name(name, sector):
    """
    Normalize a resource name.

    Parameters
    ----------
    name : str
        The resource name.
    sector : str
        The sector the resource is in.

    Returns
    -------
    str | none
        The normalized name, or None if the name is invalid and couldn't be
        normalized.
    """

    sector_match = re.match(
        r'^\s*(?P<sector>\S+)\s+(?P<ores>.+?)(_\d+)?$', name)
    if sector_match is None:
        return None

    existing_sector = sector_match.group('sector').upper()
    ores = sector_match.group('ores').upper()

    if existing_sector in ORES:
        # If sector is an ore just assume sector is missing and continue.
        ores = f'{existing_sector} {ores}'
    elif not valid_sector(existing_sector):
        sys.stderr.write(f'Invalid sector: {existing_sector}\n')
        return None

    valid_ores = []
    for ores_match in re.finditer(
            r'\s*(?P<ore>[A-Z]+)(\s+(?P<size>[^,]+)\s*,?)?', ores):
        ore = ores_match.group('ore')
        size = ores_match.group('size')
        if size is not None:
            size = size.strip()

        if ore not in ORES:
            sys.stderr.write(f'Invalid ore: {ore}\n')
            return None

        valid_ores.append((ore, size))

    valid_ores.sort(key=lambda valid_ore: ORES.index(valid_ore[0]))

    normalized_name = f"{sector}"
    first = True
    for valid_ore in valid_ores:
        if first:
            first = False
            normalized_name += ' '
        else:
            normalized_name += ' , '

        (ore_name, ore_size) = valid_ore
        normalized_name += ore_name
        if ore_size is not None:
            normalized_name += f' {ore_size}'

    return normalized_name


def valid_sector(sector_abbr):
    """
    Check if the provided sector_abbr is valid.

    Parameters
    ----------
    sector_abbr : str
        The sector abbreviation to check.

    Returns
    -------
    bool
        True if it's a valid sector abbreviation, False otherwise.
    """

    for sector in SECTORS:
        if sector['abbr'] == sector_abbr:
            return True
    return False


def make_names_unique(resources):
    """
    Make every resource name unique. This makes it easier to identify GPS
    coordinates in the GPS list.

    Parameters
    ----------
    resources : list
        List of resource coordinates. The names are updated so each name is
        unique.
    """

    name_hash = {}

    for resource in resources:
        name = resource['name']
        if name in name_hash:
            resource['name'] = f'{name} _{name_hash[name]}'
            name_hash[name] += 1
        else:
            name_hash[name] = 2


if __name__ == '__main__':
    main()
