import math
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import Point, LineString
from pyproj import Geod

def round_coords(x, y = None, signif = 15):
    '''
    Round coordinates to match the precision used by DJI.

    Parameters
    ----------
    x : float or list/tuple of float
        First input coordinate.
    y : float, optional
        Second input coordinate. The default is None.
    signif : int, optional
        Number of significant digits. The default is 15.

    Returns
    -------
    x1(, y1) : float
        Rounded coordinate(s). Format matches input

    '''
    if isinstance(x, (list, tuple)):
        (x, y) = x
    
    x1 = float("%.*g" % (signif, x))
    
    if y is not None:
        y1 = float("%.*g" % (signif, y))
        
        if isinstance(x, (list, tuple)):
            return (x1, y1)
        else:
            return x1, y1
    else:
        return x1

def coordinates_to_utm(lon, lat, utm_crs = None):
    """
    Convert geographic coordinates (longitude, latitude) to UTM coordinates.

    Parameters
    ----------
    lon : float
        Longitude in decimal degrees.
    lat : float
        Latitude in decimal degrees.
    utm_crs : str
        UTM coordinate reference system (CRS) to use for the conversion.

    Returns
    -------
    tuple
        UTM coordinates (easting, northing) in meters.
    """
    # Create a GeoDataFrame with the input coordinates
    gdf = gpd.GeoDataFrame(
        geometry = [Point(lon, lat)],
        crs = "EPSG:4326"
    )

    utm_crs = gdf.estimate_utm_crs() if utm_crs is None else utm_crs

    # Convert to the specified UTM CRS
    gdf_utm = gdf.to_crs(utm_crs)

    # Extract the UTM coordinates
    easting, northing = gdf_utm.geometry.x[0], gdf_utm.geometry.y[0]

    return easting, northing

def waypoint_distance(wp0, wp1):
    """
    Calculate the distance between two waypoints.

    Parameters
    ----------
    wp0 : Waypoint
        The first waypoint.
    wp1 : Waypoint
        The second waypoint.

    Returns
    -------
    float
        The distance between the two waypoints in meters.
    """
    g = Geod(ellps = "WGS84")
    
    lon1, lat1 = wp0.coordinates
    lon2, lat2 = wp1.coordinates
    
    alt0 = wp0.altitude
    alt1 = wp1.altitude
    
    horizontal, _, _ = g.inv(lon1, lat1, lon2, lat2)
    vertical = alt1 - alt0

    distance_3d = math.sqrt(horizontal ** 2 + vertical ** 2)
    
    return distance_3d

def segment_duration(wp0, wp1):
    """
    Calculate the duration of a flight segment between two waypoints.

    Parameters
    ----------
    wp0 : Waypoint
        The starting waypoint.
    wp1 : Waypoint
        The ending waypoint.

    Returns
    -------
    float
        The duration of the flight segment in seconds.
    """
    speed = wp0.velocity
    distance = waypoint_distance(wp0, wp1)
    duration = distance / speed if speed > 0 else None

    return duration

def segment_altitude(
        dsm_path,
        waypoints,
        altitude_agl,
        horizontal_safety_buffer_m = 10.
    ):
    if isinstance(waypoints, (tuple, list)):
        try:
            segment_coords = [wpt.coordinates for wpt in waypoints]
        except:
            raise Exception("Failed to read coordinates from waypoint list.")
        
        segment_linestring = gpd.GeoDataFrame(
            geometry = [LineString(segment_coords)], crs = "EPSG:4326"
            )
    else:
        raise TypeError(
            f"Invalid type for waypoints: {type(waypoints)}. " +
            "Expected list/tuple of Waypoint objects."
            )
    
    utm_zone = segment_linestring.estimate_utm_crs(datum_name = "WGS 84")
    
    buffered_segment = segment_linestring.to_crs(utm_zone)
    buffered_segment = buffered_segment.buffer(
        horizontal_safety_buffer_m
        )
    buffered_segment = buffered_segment.to_crs(
        "EPSG:4326"
        )
    
    # Mask DSM to the buffered object
    with rasterio.open(dsm_path) as dsm_file:
        dsm_file_masked, dsm_file_masked_transform = rasterio.mask.mask(
            dsm_file, buffered_segment, crop = True, indexes = 1)
        dsm_file_masked[dsm_file_masked == dsm_file.nodatavals] = np.nan

    segment_max_elevation = np.nanmax(dsm_file_masked)
    waypoint_altitude = segment_max_elevation + altitude_agl
    
    return waypoint_altitude