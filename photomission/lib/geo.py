import math
import numpy as np
import geopandas as gpd
import rasterio
from rasterio import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import Point, LineString, mapping
from pyproj import Geod
from warnings import warn

def get_utm_crs(coordinates):
    """
    Get the UTM CRS (Coordinate Reference System) for a given set of coordinates.

    Parameters
    ----------
    coordinates : tuple
        A tuple containing the (longitude, latitude) of the point.

    Returns
    -------
    str
        The UTM CRS string (e.g., "EPSG:32633" for UTM zone 33N).
    """
    lon, lat = coordinates
    gdf = gpd.GeoDataFrame(
        geometry = [Point(lon, lat)],
        crs = "EPSG:4326"
    )
    utm_crs = gdf.estimate_utm_crs()
    return utm_crs

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

def coordinates_to_lonlat(easting, northing, utm_crs):
    """
    Convert UTM coordinates to geographic coordinates (longitude,
    latitude).
    
    Parameters
    ----------
    easting : float
        Easting in meters.
    northing : float
        Northing in meters.
    utm_crs : str
        UTM coordinate reference system (CRS) to use for the conversion.

    Returns
    -------
    tuple
        Geographic coordinates (longitude, latitude) in decimal degrees.
    """
    if utm_crs is None:
        raise ValueError("UTM CRS must be provided for conversion.")
    
    # Create a GeoDataFrame with the input coordinates
    gdf = gpd.GeoDataFrame(
        geometry = [Point(easting, northing)],
        crs = utm_crs
    )

    # Convert to geographic coordinates (WGS84)
    gdf_wgs84 = gdf.to_crs("EPSG:4326")

    # Extract the geographic coordinates
    lon, lat = gdf_wgs84.geometry.x[0], gdf_wgs84.geometry.y[0]

    return lon, lat

def coordinates_to_utm(lon, lat, utm_crs = None, return_utm_zone = False):
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
    return_utm_zone : bool
        Whether to return the UTM zone information.
    
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

    if return_utm_zone:
        return easting, northing, utm_crs
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
    
    _, _, horizontal = g.inv(lon1, lat1, lon2, lat2)

    if alt0 is None or alt1 is None:
        vertical = 0
        warn(
            "Altitude information is missing for one or both " +
            "waypoints. Cannot compute accurrate distance."
            )
    else:
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
        wpt0,
        wpt1,
        altitude_agl,
        horizontal_safety_buffer_m = 20.
    ):
    try:
        segment_coords = [wpt.coordinates for wpt in [wpt0, wpt1]]
    except:
        raise Exception("Failed to read coordinates from waypoins.")
    
    segment_linestring = gpd.GeoDataFrame(
        geometry = [LineString(segment_coords)], crs = "EPSG:4326"
        )
    
    utm_zone = wpt0.utm_crs
    
    buffered_segment_utm = segment_linestring.to_crs(utm_zone)
    buffered_segment_utm_buffered = buffered_segment_utm.buffer(
        horizontal_safety_buffer_m
        )
    buffered_segment = buffered_segment_utm_buffered.to_crs("EPSG:4326")
    shapes = [mapping(geom) for geom in buffered_segment.geometry]
    # Mask DSM to the buffered object
    with rasterio.open(dsm_path) as dsm_file:
        crs_src = dsm_file.crs
        crs_dst = "EPSG:4326"
        
        if crs_src != crs_dst:
            raise NotImplementedError(
                "Input raster CRS is not EPSG:4326. CRS transformation is not implemented."
            )
        dsm_file_masked, _ = mask.mask(
            dsm_file, shapes,
            crop = True,
            indexes = 1,
            all_touched = True
            )
        dsm_file_masked = dsm_file_masked.astype(float)
        if isinstance(dsm_file.nodatavals, (tuple, list)):
            for nd in dsm_file.nodatavals:
                if nd is not None and np.isfinite(nd):
                    dsm_file_masked[np.isclose(dsm_file_masked, nd)] = np.nan
        else:
            dsm_file_masked[
                np.isclose(dsm_file_masked, dsm_file.nodatavals)
                ] = np.nan
    
    segment_max_elevation = np.nanmax(dsm_file_masked)
    if np.isnan(segment_max_elevation):
        raise ValueError(
            "No DSM data found along the flight segment between " +
            f"{wpt0.coordinates} and {wpt1.coordinates}. " +
            "Cannot determine flight altitude."
            )

    # Provide additional safety in case of IMU calibration
    if wpt0.perform_imu_calibration:
        buffer_dist = 30.
        for actiongroup in wpt0.actions:
            for action in actiongroup.actions:
                if hasattr(action, "calibrationDistance"):
                    buffer_dist = action.calibrationDistance
        
        gdf = gpd.GeoDataFrame(
            geometry = [Point(wpt0.coordinates[0], wpt0.coordinates[1])],
            crs = "EPSG:4326"
            )
        gdf_utm = gdf.to_crs(utm_zone)
        polygon = gdf_utm.geometry[0].buffer(buffer_dist)
        polygon_4326 = gpd.GeoSeries(
            [polygon], crs = utm_zone
            ).to_crs("EPSG:4326")[0]
        with rasterio.open(dsm_path) as dsm_file:
            dsm_file_masked, _ = mask.mask(
                dsm_file, [mapping(polygon_4326)],
                crop = True,
                indexes = 1,
                all_touched = True
                )
            dsm_file_masked = dsm_file_masked.astype(float)
            if isinstance(dsm_file.nodatavals, (tuple, list)):
                for nd in dsm_file.nodatavals:
                    if nd is not None and np.isfinite(nd):
                        dsm_file_masked[np.isclose(dsm_file_masked, nd)] = np.nan
            else:
                dsm_file_masked[
                    np.isclose(dsm_file_masked, dsm_file.nodatavals)
                    ] = np.nan
            circle_max_elevation = np.nanmax(dsm_file_masked)
        
        segment_max_elevation = np.nanmax([
            segment_max_elevation, circle_max_elevation
            ])
    if np.isnan(segment_max_elevation):
        raise ValueError(
            "No DSM data found along the flight segment between " +
            f"{wpt0.coordinates} and {wpt1.coordinates}, " +
            "nor in the IMU calibration area around " +
            f"{wpt0.coordinates}. Cannot determine flight altitude."
            )
    if segment_max_elevation <= 0.0:
        warn(
            "Maximum DSM elevation along the flight segment and " +
            "in the IMU calibration area is <= zero. This seems " +
            "unlikely. Please check your DSM data."
            )
    
    waypoint_altitude = segment_max_elevation + altitude_agl
    
    return waypoint_altitude

def waypoint_altitude(dsm_path, wpt, altitude_agl = 0.0):
    """
    Get the altitude of a waypoint based on DSM data.

    Parameters
    ----------
    dsm_path : str
        The file path to the DSM (Digital Surface Model) raster.
    wpt : Waypoint
        The waypoint for which to retrieve the altitude.
    altitude_agl : float, optional
        The altitude above ground level (AGL) to add to the DSM value.

    Returns
    -------
    float
        The calculated altitude for the waypoint.
    """
    coordinates = wpt.coordinates

    with rasterio.open(dsm_path) as src:
        if not src.crs.is_geographic:
            raise NotImplementedError(
                "Input raster CRS is not EPSG:4326. CRS transformation is not implemented."
            )
        dsm_value = list(src.sample([coordinates]))[0][0]
        
        if dsm_value == src.nodata:
            raise ValueError(f"No DSM data at location {coordinates}")
    
    if np.isnan(dsm_value):
        raise ValueError(f"DSM value is NaN at location {coordinates}")
    
    if dsm_value <= 0:
        warn(
            f"DSM value is ({dsm_value} m) at location " +
            f"{coordinates}. This seems unlikely. Check DSM data."
            )
    
    altitude = dsm_value + altitude_agl
    
    return altitude