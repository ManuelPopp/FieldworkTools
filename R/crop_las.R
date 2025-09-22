rm(list = ls())
#-------------------------------------------------------------------------------
#> Import packages
import <- function(...) {
  #' Import R packages. Install them if necessary.
  #' 
  #' @param ... any argument that can be passed to install.packages.
  #' @details The function installs only packages that are missing. Packages
  #' are loaded.
  #' @examples
  #' # Load packages
  #' import("dplyr", "MASS", "terra", dependencies = TRUE)
  #' 
  #' @seealso \code{\link[base]{install.packages}}
  #' @export
  args <- list(...)
  packages = args[names(args) == ""]
  kwargs = args[names(args) != ""]
  
  for (package in packages) {
    if (!require(package, character.only = TRUE)) {
      do.call(install.packages, c(list(package), kwargs))
    }
    require(package, character.only = TRUE)
  }
}

import(
  "terra", "tidyterra", "lidR",
  dependencies = TRUE
)

#-------------------------------------------------------------------------------
#> Read command-line arguments
# Usage: Rscript crop_las.R input.las polygon.kml output.las
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) {
  stop("Usage: Rscript crop_las.R <input_las> <vector_file> <output_las>")
}

f_pointcloud <- args[1]
f_bounds <- args[2]
f_output <- args[3]

#-------------------------------------------------------------------------------
#> Read point cloud
las <- lidR::readLAS(f_pointcloud)

if (is.empty(las)) {
  stop("Point cloud is empty or could not be read.")
}

#-------------------------------------------------------------------------------
#> Get bounding box
extent <- terra::vect(f_bounds) %>%
  terra::project(y = paste0("epsg:", sf::st_crs(lidR::crs(las))$epsg)) %>%
  terra::ext()

intersects <- terra::vect(sf::st_as_sfc(lidR::st_bbox(las))) %>%
  terra::is.related(extent, "intersects")

if (!intersects) {
  stop("Point cloud and cropping box extents do not intersect.")
}

#-------------------------------------------------------------------------------
#> Crop point cloud
lidR::readLAS(f_pointcloud) %>%
  lidR::clip_rectangle(extent$xmin, extent$ymin, extent$xmax, extent$ymax) %>%
  lidR::writeLAS(f_output)