import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from pyproj import Geod
from warnings import warn
from lib.geo import coordinates_to_utm, coordinates_to_lonlat

def bearing_to_math(angle_deg):
    return (90 - angle_deg) % 360

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

def free_angle_flight_path(
        centre_easting, centre_northing, local_crs,
        top, bottom, left, right,
        rectangle_rotation_angle, flight_angle,
        line_spacing, buffer_m, start_point = None
        ):
    """
    Generates waypoints for an S-shaped drone flight path over a rectangular plot,
    extending the flight area by a specified buffer on all sides. All waypoints
    will lie precisely on the perimeter of this buffered area.

    Input defines the rectangle by its centre, dimensions, and rotation.
    Waypoints are calculated in UTM space and then converted back to Latitude and Longitude.
    The flight lines will be tilted by the specified flight_angle relative to East.

    Args:
        centre_lat (float): Latitude of the rectangle's centre.
        centre_lon (float): Longitude of the rectangle's centre.
        width (float): Width of the rectangle in meters (along its local x-axis).
        height (float): Height of the rectangle in meters (along its local y-axis).
        rectangle_rotation_angle (float): Rotation of the rectangle in degrees,
                                          relative to East (positive x-axis in UTM).
                                          0 degrees means width is along East-West.
        flight_angle (float): The flight path angle in degrees relative to the
                              positive x-axis (East in UTM).
        line_spacing (float): The distance between parallel flight lines in meters.
        buffer_m (float): The distance in meters by which to extend the flight
                          area beyond the original rectangle's boundaries.

    Returns:
        tuple: A tuple containing:
            - list of tuples: A list of (latitude, longitude) coordinates representing
                              the waypoints for the drone flight.
            - list of tuples: A list of (latitude, longitude) coordinates representing
                              the corners of the buffered rectangle.
            - list of tuples: A list of (latitude, longitude) coordinates representing
                              the corners of the original rectangle.
    """
    flight_angle = (flight_angle - 90) % 360
    # 1. Convert centre lat-lon to UTM
    original_centroid_utm = np.array([centre_easting, centre_northing])

    # Corners of an axis-aligned rectangle centreed at (0,0)
    base_corners_relative_to_origin = np.array([
        [left, bottom],
        [right, bottom],
        [right, top],
        [left, top]
    ]) - original_centroid_utm

    # Rotate these base corners by the rectangle's rotation angle
    rect_rotation_rad = np.deg2rad(360 - rectangle_rotation_angle)
    rect_rotation_matrix = np.array([
        [np.cos(rect_rotation_rad), -np.sin(rect_rotation_rad)],
        [np.sin(rect_rotation_rad), np.cos(rect_rotation_rad)]
    ])
    rotated_corners_relative_to_origin = base_corners_relative_to_origin \
        @ rect_rotation_matrix.T
    
    # Translate rotated corners to their absolute UTM positions
    rect_coords_np_utm = rotated_corners_relative_to_origin + \
        original_centroid_utm
    
    # The orientation of the original rectangle is simply its rotation angle
    original_rect_orientation_rad = np.deg2rad(360 - rectangle_rotation_angle)
    # 3. Calculate the buffered rectangle's corners in UTM
    # Rotate the centered original rectangle to be axis-aligned to its own orientation
    align_rotation_matrix = np.array([
        [
            np.cos(-original_rect_orientation_rad),
            -np.sin(-original_rect_orientation_rad)
            ],
        [np.sin(-original_rect_orientation_rad),
         np.cos(-original_rect_orientation_rad)
         ]
    ])
    original_rect_axis_aligned = (
        rect_coords_np_utm - original_centroid_utm
        ) @ align_rotation_matrix.T
    
    # Find the bounds of this axis-aligned original rectangle
    x_min_aligned, y_min_aligned = np.min(original_rect_axis_aligned, axis = 0)
    x_max_aligned, y_max_aligned = np.max(original_rect_axis_aligned, axis = 0)

    # Apply the buffer to these axis-aligned dimensions
    buffered_x_min_aligned = x_min_aligned - buffer_m
    buffered_x_max_aligned = x_max_aligned + buffer_m
    buffered_y_min_aligned = y_min_aligned - buffer_m
    buffered_y_max_aligned = y_max_aligned + buffer_m

    # Form the corners of this axis-aligned, buffered rectangle
    buffered_corners_aligned = np.array([
        [buffered_x_min_aligned, buffered_y_min_aligned],
        [buffered_x_max_aligned, buffered_y_min_aligned],
        [buffered_x_max_aligned, buffered_y_max_aligned],
        [buffered_x_min_aligned, buffered_y_max_aligned]
    ])

    # Rotate this buffered rectangle back to the original orientation and translate back
    unalign_rotation_matrix = np.array([
        [np.cos(original_rect_orientation_rad), -np.sin(original_rect_orientation_rad)],
        [np.sin(original_rect_orientation_rad), np.cos(original_rect_orientation_rad)]
    ])
    buffered_rect_corners_utm = (
        buffered_corners_aligned @ unalign_rotation_matrix.T
        ) + original_centroid_utm

    # Calculate the centroid of this newly defined, rotated buffered rectangle
    centroid_of_buffered_rect_utm = np.mean(buffered_rect_corners_utm, axis = 0)

    # centre the BUFFERED rectangle around its own centroid for flight path rotation
    centreed_buffered_rect_for_flight_rotation = buffered_rect_corners_utm - \
        centroid_of_buffered_rect_utm
    

    line_direction = -1  # 1 for moving up (increasing y in rotated system), -1 for moving down
    # Adjust line direction and rotation based on start point
    if start_point is not None:
        start_lon, start_lat = start_point
        start_e, start_n = coordinates_to_utm(
            start_lon, start_lat, utm_crs = local_crs
            )
        start_point_utm = np.array([start_e, start_n])
        dists = [
            np.linalg.norm(np.array(c) - start_point_utm)
                for c in buffered_rect_corners_utm
            ]
        nearest_corner = np.argmin(dists)
        expected_corner = 0
        if nearest_corner != expected_corner:
            # if it is the opposite diagonal corner → rotate by 180 degrees
            if (nearest_corner - expected_corner) % 2 == 0:
                flight_angle += 180
            else:
                line_direction *= -1
    
    # Convert flight angle from degrees to radians
    flight_angle_rad = np.deg2rad(flight_angle)

    # Create a rotation matrix for the flight path.
    flight_path_rotation_matrix = np.array([
        [np.cos(flight_angle_rad), -np.sin(flight_angle_rad)],
        [np.sin(flight_angle_rad), np.cos(flight_angle_rad)]
    ])

    # Rotate the BUFFERED rectangle's corners into this new coordinate system
    # where the flight lines will be "vertical" (parallel to the new y-axis)
    rotated_buffered_rect_for_flight_path_generation = centreed_buffered_rect_for_flight_rotation @ flight_path_rotation_matrix.T

    # Define the four sides of this *rotated buffered rectangle* as line segments
    rotated_buffered_sides_for_flight_path_generation = [
        (rotated_buffered_rect_for_flight_path_generation[0], rotated_buffered_rect_for_flight_path_generation[1]),
        (rotated_buffered_rect_for_flight_path_generation[1], rotated_buffered_rect_for_flight_path_generation[2]),
        (rotated_buffered_rect_for_flight_path_generation[2], rotated_buffered_rect_for_flight_path_generation[3]),
        (rotated_buffered_rect_for_flight_path_generation[3], rotated_buffered_rect_for_flight_path_generation[0])
    ]

    # Find the bounds of the rotated BUFFERED rectangle for the flight path's x-range
    x_min_flight_aligned, _ = np.min(rotated_buffered_rect_for_flight_path_generation, axis=0)
    x_max_flight_aligned, _ = np.max(rotated_buffered_rect_for_flight_path_generation, axis=0)

    waypoints_rotated_for_flight = []
    current_x_rotated = x_min_flight_aligned
    
    # Iterate through x-coordinates in the flight-aligned rotated system to create parallel lines
    while current_x_rotated <= x_max_flight_aligned + line_spacing / 2:
        intersections = []
        for p1, p2 in rotated_buffered_sides_for_flight_path_generation:
            x1, y1 = p1
            x2, y2 = p2

            if np.isclose(x1, x2): # Vertical segment in rotated space
                if np.isclose(x1, current_x_rotated):
                    intersections.extend([y1, y2])
            else:
                t = (current_x_rotated - x1) / (x2 - x1)
                if 0 <= t <= 1 and \
                   (
                       (
                           min(x1, x2) <= current_x_rotated <= max(x1, x2)
                           ) or np.isclose(
                               min(x1, x2), current_x_rotated
                               ) or np.isclose(
                                   max(x1, x2), current_x_rotated
                                   )
                                   ):
                    y_intersection = y1 + t * (y2 - y1)
                    intersections.append(y_intersection)

        if len(intersections) >= 2:
            y_min_line = min(intersections)
            y_max_line = max(intersections)

            if line_direction == 1:
                waypoints_rotated_for_flight.append((current_x_rotated, y_min_line))
                waypoints_rotated_for_flight.append((current_x_rotated, y_max_line))
            else:
                waypoints_rotated_for_flight.append((current_x_rotated, y_max_line))
                waypoints_rotated_for_flight.append((current_x_rotated, y_min_line))

        current_x_rotated += line_spacing
        line_direction *= -1

    # Rotate the waypoints back from the flight-aligned system to the original UTM system
    inverse_flight_path_rotation_matrix = np.linalg.inv(flight_path_rotation_matrix)
    final_waypoints_utm = []
    for point_rotated in waypoints_rotated_for_flight:
        rotated_point_utm = np.array(point_rotated) @ inverse_flight_path_rotation_matrix.T
        final_waypoints_utm.append(tuple(rotated_point_utm + centroid_of_buffered_rect_utm))

    # 4. Convert final UTM waypoints and buffered rectangle corners back to Lat-Lon
    final_waypoints_lonlat = []
    for easting, northing in final_waypoints_utm:
        lon, lat = coordinates_to_lonlat(easting, northing, utm_crs = local_crs)
        final_waypoints_lonlat.append((lon, lat))

    buffered_rect_corners_latlon = []
    for easting, northing in buffered_rect_corners_utm:
        lon, lat = coordinates_to_lonlat(easting, northing, utm_crs = local_crs)
        buffered_rect_corners_latlon.append((lat, lon))

    original_rect_corners_latlon = []
    for easting, northing in rect_coords_np_utm:
        lon, lat = coordinates_to_lonlat(
            easting, northing, utm_crs = local_crs
            )
        original_rect_corners_latlon.append((lon, lat))
    
    coord_df = pd.DataFrame(final_waypoints_lonlat, columns = ["x", "y"])
    
    return coord_df, buffered_rect_corners_latlon, original_rect_corners_latlon

def simple_grid(
        top, bottom, left, right, x_centre, y_centre, spacing, buffer,
        plotangle, gridmode, local_crs
        ):
    top_shrunk = top - 0.5 * spacing
    bottom_shrunk = bottom + 0.5 * spacing
    span = (top_shrunk + 2 * buffer - bottom_shrunk)
    n_parts = int(span // spacing)
    offset = (span - n_parts * spacing) / 2
    start = bottom_shrunk - buffer + offset
    end = top_shrunk + buffer
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

    if gridmode == "simple":
        right_shrunk = right - 0.5 * spacing
        left_shrunk = left + 0.5 * spacing
        span = (right_shrunk + 2 * buffer - left_shrunk)
        n_parts = int(span // spacing)
        offset = (span - n_parts * spacing) / 2
        start = left_shrunk - buffer + offset
        end = right_shrunk + buffer

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

def double_grid(
        top, bottom, left, right, x_centre, y_centre, spacing, buffer,
        plotangle, local_crs
        ):
    base_grid_coordinates = simple_grid(
        top, bottom, left, right, x_centre, y_centre, spacing, buffer,
        plotangle, gridmode = "simple", local_crs = local_crs
        )
    last_point = (
        base_grid_coordinates.iloc[-1,].x,
        base_grid_coordinates.iloc[-1,].y
        )
    
    rotation_45_grid_coordinates, _, _ = free_angle_flight_path(
        centre_northing = y_centre, centre_easting = x_centre,
        local_crs = local_crs,
        top = top, bottom = bottom, left = left, right = right,
        rectangle_rotation_angle = plotangle,
        flight_angle = plotangle + 45,
        line_spacing = spacing, buffer_m = buffer,
        start_point = last_point
        )
    last_point = (
        rotation_45_grid_coordinates.iloc[-1,].x,
        rotation_45_grid_coordinates.iloc[-1,].y
        )
    
    rotation_135_grid_coordinates, _, _ = free_angle_flight_path(
        centre_northing = y_centre, centre_easting = x_centre,
        local_crs = local_crs,
        top = top, bottom = bottom, left = left, right = right,
        rectangle_rotation_angle = plotangle,
        flight_angle = plotangle + 135,
        line_spacing = spacing, buffer_m = buffer,
        start_point = last_point
        )
    
    double_grid_coordinates = pd.concat(
        [
            base_grid_coordinates,
            rotation_45_grid_coordinates,
            rotation_135_grid_coordinates
            ],
        ignore_index = True
        )
    
    return double_grid_coordinates