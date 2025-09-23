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
  "lidR",
  dependencies = TRUE
)

#-------------------------------------------------------------------------------
#> Read command-line arguments
# Usage: Rscript crop_las.R input.las polygon.kml output.las
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) {
  stop("Usage: Rscript merge_las.R <input_las_folder> <output_las_file>")
}

src <- args[1]
dst <- args[2]

#-------------------------------------------------------------------------------
#> Load point cloud files
print("Loading files...")
las_files <- list.files(src, pattern = "\\.las$", full.names = TRUE)
if (length(las_files) < 1) {
  stop(paste0("No *.las files found in ", src, "."))
}
cat(
  "Input files:\n",
  paste(las_files, collapse = "\n")
  )

las_list <- lapply(las_files, lidR::readLAS)

#-------------------------------------------------------------------------------
#> Merge point cloud files
merged_las <- do.call(rbind, las_list)

#-------------------------------------------------------------------------------
#> Write to disc
lidR::writeLAS(merged_las, dst)