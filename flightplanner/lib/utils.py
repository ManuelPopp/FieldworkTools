import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from warnings import warn

# Functions-------------------------------------------------------------
def get_heading_angle(p0, p1):
    """
    Compute the heading angle (azimuth) between two waypoints.

    Parameters
    ----------
    p0 : Waypoint
        Coordinates of the first point (longitude, latitude).
    p1 : Waypoint
        Coordinates of the second point (longitude, latitude).
    
    Returns
    -------
    float
        Heading angle in degrees.
    
    """
    dx = p1.coordinates_utm[0] - p0.coordinates_utm[0]
    dy = p1.coordinates_utm[1] - p0.coordinates_utm[1]
    phi = round(np.degrees(np.arctan2(dx, dy)), 1)
    
    if phi > 180:
        phi -= 360
    elif phi <= -180:
        phi += 360
    
    return phi

# Experimental, not working---------------------------------------------
def get_overlaps(
        horizontalfov, secondary_hfov, altitude, spacing, overlapsensor,
        side_overlap, front_overlap
        ):
        """NOT WORKING! NOT WORKING! NOT WORKING! NOT WORKING! NOT WORKING!
        Calculate the overlaps for the flight pattern based on the
        horizontal field of view, secondary horizontal field of view,
        altitude, spacing, and overlap sensor.

        Parameters
        ----------
        horizontalfov : float
            Horizontal field of view in degrees.
        secondary_hfov : float
            Secondary horizontal field of view in degrees.
        altitude : float
            Flight altitude in meters.
        spacing : float
            Flight spacing in meters.
        overlapsensor : str
            Overlap sensor type.
        side_overlap : float
            Side overlap as a fraction (0 to 1).
        front_overlap : float
            Front overlap as a fraction (0 to 1).
        
        Returns
        -------
        tuple
            Tuple containing the left side overlap, left width overlap,
            centre side overlap, and centre width overlap.
        
        """
        if overlapsensor.lower() in ["rgb", "ms"]:
            lsolaph = colaph = front_overlap
            lsolapw = colapw = side_overlap

        if overlapsensor.lower() == "ls":
            #side_ol_main = 2 - spacing / (
            #    np.tan((horizontalfov / 2) * np.pi / 180) * altitude
            #    )
            try:
                side_ol_sec = (
                    2 - spacing / (
                        np.tan((secondary_hfov / 2) * np.pi / 180) * altitude
                        )
                    ) * 100
            except TypeError as e:
                warn(
                    f"Error calculating side overlap: {e}. Using side " +
                    f"overlap {side_overlap} for secondary sensor."
                    )
                side_ol_sec = side_overlap
            
            lsolaph = front_overlap
            lsolapw = side_overlap
            colaph = front_overlap
            colapw = side_ol_sec
        
        return (lsolaph, lsolapw, colaph, colapw)

def photo_trigger_intervals(
        front_overlap_fraction, vertical_fov, altitude, velocity
        ):
    """NOT WORKING! NOT WORKING! NOT WORKING! NOT WORKING! NOT WORKING!
    Calculate the time interval between photo triggers based on the
    front overlap fraction, vertical field of view, altitude, and velocity.
    
    Parameters
    ----------
    front_overlap_fraction : float
        Fraction of front overlap (0 to 1).
    vertical_fov : float
        Vertical field of view in degrees.
    altitude : float
        Flight altitude in meters.
    velocity : float
        Flight velocity in m/s.
    
    Returns
    -------
    float
        Time interval between photo triggers in seconds.
    
    """
    try:
        fov_half = vertical_fov / 2 * np.pi / 180
        delta_t = (
            2 - front_overlap_fraction
            ) * np.tan(fov_half) * altitude / velocity
        return delta_t
    except ZeroDivisionError as e:
        warn(f"Error calculating photo trigger intervals: {e}. Using default.")
    except TypeError as e:
        warn(f"Error calculating photo trigger intervals: {e}. Using default.")
    return 1.0

def get_mapping_vertical_fov(args):
    """
    Get the mapping for vertical field of view (FOV).
    """
    if args.overlapsensor.lower() in ["rgb", "ms"]:
        fov = args.verticalfov
    else:
        fov = args.secondary_vfov
    
    return fov

def get_photo_trigger_intervals(args):
    lsolaph, lsolapw, colaph, colapw = get_overlaps(
        horizontalfov, secondary_hfov, altitude, spacing, overlapsensor,
        side_overlap, front_overlap
    )
    action_trigger = photo_trigger_intervals(
        front_overlap_fraction = colapw / 100,
        vertical_fov = get_mapping_vertical_fov(),
        altitude = args.altitude,
        velocity = args.flightspeed
        )
    return action_trigger