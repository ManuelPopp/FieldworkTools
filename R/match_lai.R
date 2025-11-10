require("terra")
require("tidyterra")
require("dplyr")
require("readxl")

extract_values <- function(raster, locations, radius = 3) {
  circles <- terra::buffer(locations, width = radius)
  extracted <- terra::extract(
    raster, circles, fun = "mean", cells = FALSE, ID = FALSE
    )
  return(extracted)
}

match_lai <- function(folder, index = "NDVI", radius = 3) {
  f_rst <- file.path(folder, "DJITerra", paste0(index, ".tif"))
  f_lai <- file.path(
    folder, "Licor", paste0(basename(folder), "_Processed_coords.xlsx")
    )
  
  if (file.exists(f_rst) & file.exists(f_lai)) {
    rst <- terra::rast(f_rst)
    #lai <- read.csv(f_lai)
    d_lai <- readxl::read_xlsx(
      path = f_lai
      )[, c("X", "Y", "LAI", "LAI_File")] %>%
      dplyr::mutate(
        sample = tools::file_path_sans_ext(LAI_File)
        ) %>%
      dplyr::group_by(sample) %>%
      dplyr::summarise(
        lat = first(X),
        lon = first(Y),
        lai = mean(LAI)
      )
    
    lai_vect <- terra::vect(
      d_lai, geom = c("lat", "lon"), crs = "epsg:4326"
      ) %>%
      terra::project(rst)
    
    index_vals <- extract_values(
      raster = rst,
      locations = lai_vect, radius = radius
    )
    
    lai_vals <- lai_vect$lai
    df <- data.frame(
      index_value = unname(index_vals), lai = lai_vals
    )
  } else {
    df <- data.frame(index_value = c(NA), lai = c(NA))
  }
  df$plot <- basename(folder)
  return(df)
}

plots <- list.dirs("E:/FIELDWORK", recursive = FALSE)

df <- do.call(
  rbind,
  lapply(X = plots, FUN = match_lai)
)
df
