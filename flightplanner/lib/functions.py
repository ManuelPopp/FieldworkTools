# Functions-------------------------------------------------------------
def get_heading_angle(p0, p1, utm_crs, src_crs = "EPSG:4326"):
    """
    Compute the heading angle (azimuth) between two waypoints.

    Parameters
    ----------
    p0 : tuple
        Coordinates of the first point (longitude, latitude).
    p1 : tuple
        Coordinates of the second point (longitude, latitude).
    utm_crs : str
        UTM coordinate reference system (CRS) to use for the calculation.
    src_crs : str, optional
        Source CRS of the input points, by default "EPSG:4326".
    
    Returns
    -------
    float
        Heading angle in degrees.
    
    """
    pdf = pd.DataFrame({
        "ID": [0, 1],
        "Latitude": [p0[0], p1[0]],
        "Longitude": [p0[1], p1[1]]
    })
    
    pgdf = gpd.GeoDataFrame(
        pdf,
        geometry = gpd.points_from_xy(pdf.Longitude, pdf.Latitude),
        crs = "EPSG:4326"
        )
    
    pgdf_utm = pgdf.to_crs(utm_crs)
    coords = pgdf_utm.get_coordinates()
    dx = coords.x[1] - coords.x[0]
    dy = coords.y[1] - coords.y[0]
    phi = np.arctan(dy / dx) / np.pi * 180

    return phi

def lines_horizontal(
        left, right, start, end, buffer = args.buffer, spacing = args.spacing,
        longitude = args.longitude, latitude = args.latitude
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
    longitude : float, optional
        The longitude of the flight area, by default args.longitude.
    latitude : float, optional
        The latitude of the flight area, by default args.latitude.

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

    final_point = gpd.GeoDataFrame(
        geometry = [Point(longitude, latitude)],
        crs = "EPSG:4326"
    )

    final_point_utm = final_point.to_crs(local_crs)

    return pd.concat(
        [wayline_gdf_utm, final_point_utm], ignore_index = True
        )

def lines_vertical(
        top, bottom, start, end, buffer = args.buffer, spacing = args.spacing,
        longitude = args.longitude, latitude = args.latitude, start_x = None
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
    longitude : float, optional
        The longitude of the flight area, by default args.longitude.
    latitude : float, optional
        The latitude of the flight area, by default args.latitude.
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

    final_point = gpd.GeoDataFrame(
        geometry = [Point(longitude, latitude)],
        crs = "EPSG:4326"
    )

    final_point_utm = final_point.to_crs(local_crs)

    return pd.concat(
        [wayline_gdf_utm, final_point_utm], ignore_index = True
        )

def rotate_gdf(gdf, x_centre, y_centre, angle):
    """
    Rotate a GeoDataFrame around a specified centre point by a given angle.

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

def get_mapping_vertical_fov():
    """
    Get the mapping for vertical field of view (FOV).
    """
    if args.overlapsensor.lower() in ["rgb", "ms"]:
        fov = args.verticalfov
    else:
        fov = args.secondary_vfov
    
    return fov