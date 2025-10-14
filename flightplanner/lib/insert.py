import numpy as np
from lib.waypoints import Waypoint
from lib.geo import coordinates_to_lonlat

def interpolate_waypoints(wp0, wp1, num_wpts):
    """
    Generate a number of intermediate waypoints along a segment defined
    by the two input waypoints.

    Parameters
    ----------
    wp0 : Waypoint
        The starting waypoint.
    wp1 : Waypoint
        The ending waypoint.
    num_wpts : int
        The number of intermediate waypoints to generate.

    Returns
    -------
    list of Waypoint
        A list of interpolated waypoints.
    """
    if num_wpts < 1:
        return []
    
    # Linear interpolation between waypoints
    utm_crs = wp0.utm_crs
    if utm_crs is None:
        raise ValueError("UTM CRS must be set for the waypoints.")
    coords_wp0 = wp0.coordinates_utm
    coords_wp1 = wp1.coordinates_utm
    x_values = np.linspace(coords_wp0[0], coords_wp1[0], num_wpts + 2)[1:-1]
    y_values = np.linspace(coords_wp0[1], coords_wp1[1], num_wpts + 2)[1:-1]
    altitudes = np.linspace(wp0.altitude, wp1.altitude, num_wpts + 2)[1:-1]
    velocities = np.linspace(wp0.velocity, wp1.velocity, num_wpts + 2)[1:-1]
    
    intermediate_waypoints = []
    for x, y, alt, vel in zip(x_values, y_values, altitudes, velocities):
        lon, lat = coordinates_to_lonlat(x, y, utm_crs)
        wpx = Waypoint(
            coordinates = (lon, lat),
            altitude = alt,
            velocity = vel,
            utm_crs = utm_crs
        )
        intermediate_waypoints.append(wpx)
    
    return intermediate_waypoints