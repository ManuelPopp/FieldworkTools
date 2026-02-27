# FieldworkTools
Scripts and tools for fieldwork.

## Content
- QGIS: Contains QGIS Python script tools and toolboxes
- bsh: Contains any batch and bash scripts (especially for the field laptop, which needs to fetch updates from this repo)
- flightplanner: A Python module for creating the LiDAR and MS fieldwork missions quickly and on site
- photomission: A Python module for creating automated photo missions for the Mavic 4 Pro
- plotplanner: A Python module to create .KMZ and .GPX files to use for orientation on smartphones and GPS devices in the field
- py3: Additional standalone Python scripts.

## Processing workflow after field sampling
1. Open each RGB file and overlay the sampling plot border.
    - If the plot area covers only forest, copy the border to a new file named <PLOTID>_final.gpkg.
    - If the plot area covers different vegetation types, crop out the forest. If it contains roads or buildings, polygonise the built-up area, buffer it by 5 m and crop it from the sampling area. In case there is sufficient sampled forest area beyond the plot area, increase the size of the original rectangle, ideally to have a 1-ha plot after masking out artificial areas. Save the masked plot areas as <PLOTID>_final.gpkg.
    - If there are power lines, use CloudCompare to remove the power lines from the LiDAR pointcloud.
2. Remove the terrain from each point cloud. Usually, the DJI Terra output is better than the DTM conputed in R or CloudCompare when using default settings. If the DJI Terra DTM is okay, just use it.
3. Use the vegetation height (DSM - DTM or DJI Terra output) to compute canopy height as mean and sd. Identify canopy gaps by applying a threshold of 5 m for high forest and 1 m for shrubland. Calculate gap metrics for each plot. If the plot contains dead trees, find a reasonable threshold for NDVI or a similar metric and compute the percentage covered by standing dead wood. Write the results to a file named <PLOTID>_plot_stats.csv.
4. Run a model to identify individual trees and conpute tree count per ha. There are various options and we need to discuss which approach to use. Add the results to <PLOTID>_plot_stats.csv.

## Contribute
It would be nice, if people from the team contribute to reach milestones faster.
If you contribute, please make sure to always stick perfectly to the style guides for the respective coding laguage:
- Python: https://peps.python.org/pep-0008/
- R: http://adv-r.had.co.nz/Style.html

In general do not end lines with spaces, avoid inconsistencies in use of quotes or spaces. Comment and---where possible---code in British English.