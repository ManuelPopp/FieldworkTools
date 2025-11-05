import os
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

base_dir = "F:/FIELDWORK/"
files_to_check = {
    ".": [
        "{PLOT}.gpx", "{PLOT}_points.gpkg", "{PLOT}_boundary.gpkg",
        "{PLOT}_L2.kmz", "{PLOT}_M3M.kmz",
        "{PLOT}_report_L2.kmz", "{PLOT}_report_M3M.kmz"
        ],
    "Licor": ["{PLOT}_Processed_coords.xlsx"],
    "DJITerra": [
        "dsm.tif", "GNDVI.tif", "LCI.tif", "NDRE.tif", "NDVI.tif", "OSAVI.tif",
        "result.tif",
        "result_Green.tif", "result_NIR.tif",
        "result_RedEdge.tif", "result_Red.tif",
        "{PLOT}.las"
}

folders = [
    f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))
    ]

data = {
    folder: {
        f"{sub}/{fname.format(PLOT = sub)}": os.path.exists(
            os.path.join(base_dir, folder, sub, fname.format(PLOT=folder))
            )
        for sub, fnames in files_to_check.items()
        for fname in fnames
        }
        for folder in folders
        }

df = pd.DataFrame(data).T
excel_path = os.path.join(base_dir, "file_check.xlsx")
df.to_excel(excel_path)

wb = load_workbook(excel_path)
ws = wb.active
green = PatternFill(
    start_color = "C6EFCE", end_color = "C6EFCE", fill_type = "solid"
    )
red = PatternFill(
    start_color = "FFC7CE", end_color = "FFC7CE", fill_type = "solid"
    )

_ = [
    ws.cell(row = r, column = c).fill = green if ws.cell(
        row = r, column = c
        ).value is True else red if ws.cell(
            row = r, column = c
            ).value is False else ws.cell(row = r, column = c).fill
            for r in range(2, ws.max_row + 1)
            for c in range(2, ws.max_column + 1)
            ]

wb.save(excel_path)