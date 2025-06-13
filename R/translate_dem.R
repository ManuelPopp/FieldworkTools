require("terra")

f_trans <- "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/org/fieldwork/chgeo2004_htrans_ETRS.agr"
f_dem <- "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/org/fieldwork/test/wsl/dsm/swissalti3d_Rameren.tif"
dir_out <- "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/org/fieldwork/Valais/dem"

translate <- function(f_dem, f_trans, f_out = NULL, dir_out = NULL, return_output = TRUE) {
  if (all(is.null(f_out), is.null(dir_out))) {
    stop("Either f_out or dir_out must not be NULL.")
  }
  
  if (is.null(f_out)) {
    if (!is.dir(dir_out)) {
      dir.create(
        dir_out,
        showWarnings = FALSE, recursive = TRUE
      )
    }
    
    f_name <- tools::file_path_sans_ext(basename(f_dem))
    f_ext <- tools::file_ext(f_dem)
    f_out <- file.path(dir_out, paste0(f_name, "_4326_ellipsoidal.", f_ext))
  }
  
  dem_4326 <- terra::rast(f_dem) %>%
    terra::project("epsg:4326")
  
  ellipsoidal_trans <- terra::rast(f_trans) %>%
    terra::resample(dem_4326)
  
  dem_out <- (dem_4326 + ellipsoidal_trans) %>%
    terra::writeRaster(filename = f_out)
  
  if (return_output) {
    return(dem_out)
  }
  
  return(NULL)
}
