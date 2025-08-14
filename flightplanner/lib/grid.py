import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from pyproj import Geod
from warnings import warn

def lines_horizontal(
        left, right, start, end, buffer, spacing, local_crs
        ):
    """
    Generate horizontal lines for the flight pattern.

    Parameters
    ----------
    left : float
        The left boundary of the flight area.
    right : float
        The right boundary of the flight area.
    start : float
        The starting y-coordinate for the flight paths.
    end : float
        The ending y-coordinate for the flight paths.
    buffer : float, optional
        The buffer distance to add to the flight paths, by default args.buffer.
    spacing : float, optional
        The spacing between flight paths, by default args.spacing.
    local_crs : str, optional
        The local coordinate reference system.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the y-coordinates of the flight paths.
    """
    y_values = np.arange(start, end, spacing)[::-1]

    n_paths = len(y_values)
    print(f"Number of flight paths: {n_paths}.")

    x_values = [left - buffer, right + buffer]
    x_coords = list()

    for i in range(n_paths):
        x_coords.extend(x_values)
        x_values.reverse()

    wayline_points_utm = pd.DataFrame({
        "y_coords": np.repeat(y_values, 2),
        "x_coords": x_coords
        })

    wayline_gdf_utm = gpd.GeoDataFrame(
        wayline_points_utm,
        geometry = gpd.points_from_xy(
            wayline_points_utm.x_coords, wayline_points_utm.y_coords
            ),
        crs = local_crs
        )
    
    return wayline_gdf_utm

def lines_vertical(
        top, bottom, start, end, buffer, spacing,
        local_crs, start_x = None
):
    """
    Generate vertical lines for the flight pattern.
    Parameters
    ----------
    top : float
        The top boundary of the flight area.
    bottom : float
        The bottom boundary of the flight area.
    start : float
        The starting x-coordinate for the flight paths.
    end : float
        The ending x-coordinate for the flight paths.
    buffer : float, optional
        The buffer distance to add to the flight paths, by default args.buffer.
    spacing : float, optional
        The spacing between flight paths, by default args.spacing.
    local_crs : str, optional
        The local coordinate reference system.
    start_x : float, optional
        The starting x-coordinate for the flight paths. If provided, the
        first x-coordinate will be adjusted to be closer to this value.
    
    Returns
    -------
    pd.DataFrame
        DataFrame containing the x-coordinates of the flight paths.
    """
    x_values = np.arange(start, end, spacing)[::-1]
    
    if start_x is not None:
        if np.abs(x_values[0] - start_x) > np.abs(x_values[-1] - start_x):
            x_values[:] = x_values[::-1]
    
    n_paths = len(x_values)
    print(f"Number of flight paths: {n_paths}.")

    y_values = [bottom - buffer, top + buffer]
    y_coords = list()

    for i in range(n_paths):
        y_coords.extend(y_values)
        y_values.reverse()

    wayline_points_utm = pd.DataFrame({
        "x_coords": np.repeat(x_values, 2),
        "y_coords": y_coords
    })

    wayline_gdf_utm = gpd.GeoDataFrame(
        wayline_points_utm,
        geometry = gpd.points_from_xy(
            wayline_points_utm.x_coords, wayline_points_utm.y_coords
            ),
        crs = local_crs
        )
    
    return wayline_gdf_utm

def rotate_gdf(gdf, x_centre, y_centre, angle):
    """
    Rotate a GeoDataFrame around a specified centre point by a given
    angle.

    Parameters
    ----------
    gdf : GeoDataFrame
        The GeoDataFrame containing the geometries to rotate.
    x_centre : float
        X coordinate of the centre point around which to rotate.
    y_centre : float
        Y coordinate of the centre point around which to rotate.
    angle : float
        Angle in degrees by which to rotate the geometries.
    """
    centre_utm = np.array([x_centre, y_centre])
    coords = np.array(gdf.get_coordinates())
    corners_rel_to_ctr = coords - centre_utm
    rect_rotation_rad = np.deg2rad(360 - angle)
    rotation_matrix = np.array([
        [np.cos(rect_rotation_rad), -np.sin(rect_rotation_rad)],
        [np.sin(rect_rotation_rad), np.cos(rect_rotation_rad)]
    ])
    rotated_corners_rel_to_ctr = corners_rel_to_ctr @ rotation_matrix.T
    coords_rotated = rotated_corners_rel_to_ctr + centre_utm
    geometries = [Point(xy) for xy in coords_rotated]
    data = {
        "Latitude": coords_rotated[:, 1],
        "Longitude": coords_rotated[:, 0],
        "geometry": geometries
    }
    return gpd.GeoDataFrame(data, crs = gdf.crs)

def get_heading_angle(p0, p1):
    geod = Geod(ellps = "WGS84")
    azimuth, _, _ = geod.inv(p0[1], p0[0], p1[1], p1[0])

    return azimuth

def estimate_lidar_forward_overlap(velocity, altitude, theta_deg = 75.):
    """
    Estimate the forward overlap for LiDAR missions based on velocity
    and altitude. (Warning: Might not work. Currently not required.)
    
    Parameters
    ----------
    velocity : float
        Flight velocity in m/s.
    altitude : float
        Flight altitude in meters.
    theta_deg : float, optional
        Scan angle in degrees, by default 75.
    
    Returns
    -------
    float
        Forward overlap as a fraction.
    
    """
    effective_scan_revisit_rate = 0.23
    warn(
        f"Actual revisit rate is unknown. Using {effective_scan_revisit_rate} s."
        )
    
    theta_rad = np.radians(theta_deg)
    fo = 1 - (
        velocity / effective_scan_revisit_rate
        ) / (
            2 * altitude * np.tan(theta_rad / 2)
            )

    return fo

def simple_grid(
        top, bottom, left, right, x_centre, y_centre, spacing, buffer,
        plotangle, gridmode, local_crs
        ):
    top -= 0.5 * spacing
    bottom += 0.5 * spacing
    span = (top + 2 * buffer - bottom)
    n_parts = int(span // spacing)
    offset = (span - n_parts * spacing) / 2
    start = bottom - buffer + offset
    end = top + buffer
    
    centre_df = pd.DataFrame({
        "ID": [1],
        "y": [y_centre],
        "x": [x_centre]
    })
    
    centre_gdf = gpd.GeoDataFrame(
        centre_df,
        geometry = gpd.points_from_xy(
            centre_df.x, centre_df.y
            ),
        crs = local_crs
        )
    
    centre_gdf.to_crs("EPSG:4326", inplace = True)
    centre_latlon = centre_gdf.get_coordinates()
    
    wayline_gdf_utm = lines_horizontal(
        left = left,
        right = right,
        start = start,
        end = end,
        buffer = buffer,
        spacing = spacing,
        local_crs = local_crs
    )

    if gridmode:
        wayline_gdf_utm = wayline_gdf_utm.iloc[:-1]
        right -= 0.5 * spacing
        left += 0.5 * spacing
        span = (right + 2 * buffer - left)
        n_parts = int(span // spacing)
        offset = (span - n_parts * spacing) / 2
        start = left - buffer + offset
        end = right + buffer

        wayline_gdf_utm_vertical = lines_vertical(
            top = top,
            bottom = bottom,
            start = start,
            end = end,
            buffer = buffer,
            spacing = spacing,
            local_crs = local_crs,
            start_x = wayline_gdf_utm.get_coordinates().iloc[-1, 0]
        )

        wayline_gdf_utm = pd.concat(
            [wayline_gdf_utm, wayline_gdf_utm_vertical],
            ignore_index = True
            )

    # Rotate flight paths if required
    if plotangle != 90:
        wayline_gdf_utm = rotate_gdf(
            gdf = wayline_gdf_utm,
            x_centre = x_centre, y_centre = y_centre,
            angle = plotangle - 90
        )

    # Convert wayline coordinates to EPSG:4326 and generate placemarks
    wayline_gdf = wayline_gdf_utm.to_crs("EPSG:4326")
    wayline_coordinates = wayline_gdf.get_coordinates()

    return wayline_coordinates