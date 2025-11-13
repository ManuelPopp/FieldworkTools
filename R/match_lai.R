require("terra")
require("tidyterra")
require("dplyr")
require("readxl")
require("ggplot2")

extract_values <- function(raster, locations, radius = 3) {
  circles <- terra::buffer(locations, width = radius)
  extracted <- terra::extract(
    raster, circles, fun = "mean", cells = FALSE, ID = FALSE
    )
  return(extracted)
}

match_lai <- function(folder, index = "NDVI", radius = 10) {
  f_rst <- file.path(folder, "DJITerra", paste0(index, ".tif"))
  f_lai <- file.path(
    folder, "Licor", paste0(basename(folder), "_Processed_coords.xlsx")
    )
  
  if (file.exists(f_rst) & file.exists(f_lai)) {
    print(paste0("File complete:", folder))
    rst <- terra::rast(f_rst)
    d_lai <- readxl::read_xlsx(
      path = f_lai
      )[, c("lon", "lat", "LAI", "LAI_File")] %>%
      dplyr::mutate(
        sample = tools::file_path_sans_ext(LAI_File)
        ) %>%
      dplyr::group_by(sample) %>%
      dplyr::summarise(
        lat = first(lat),
        lon = first(lon),
        lai = mean(LAI)
      )
    
    lai_vect <- terra::vect(
      d_lai, geom = c("lon", "lat"), crs = "epsg:4326"
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
    print(paste0("Files incomplete: ", folder))
    df <- data.frame(index_value = c(NA), lai = c(NA))
  }
  df$plot <- basename(folder)
  return(df)
}

plots <- list.dirs("F:/FIELDWORK", recursive = FALSE)

df <- do.call(
  rbind,
  lapply(X = plots, FUN = match_lai)
)

ggplot2::ggplot(
  data = df, ggplot2::aes(x = lai, y = index_value, colour = plot)
  ) +
  ggplot2::geom_point() +
  ggplot2::theme_bw()

cor.test(
  df$lai,
  df$index_value,
  method = "pearson"
)

df_corr <- df %>%
  dplyr::group_by(plot) %>%
  dplyr::summarise(
    cor_coef = cor.test(
      lai, index_value,
      method = "pearson"
    )$estimate,
    p_value = cor.test(
      lai, index_value,
      method = "pearson"
    )$p.value
  )
