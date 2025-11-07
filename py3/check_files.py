import os
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

base_dir = "F:/FIELDWORK"
files_to_check = {
    "": [
        "{PLOT}.gpx", "{PLOT}_points.gpkg", "{PLOT}_boundary.gpkg",
        "{PLOT}_L2.kmz", "{PLOT}_M3M.kmz",
        "{PLOT}_report_L2.kmz", "{PLOT}_report_M3M.kmz"
    ],
    "Licor": [
        "Above/{PLOT}-A.txt",
        "Below/{PLOT}-B.txt",
        "{PLOT}_Processed_coords.xlsx"
    ],
    "DJITerra": [
        "GNDVI.tif", "LCI.tif", "NDRE.tif", "NDVI.tif", "OSAVI.tif",
        "result.tif", "result_Green.tif", "result_NIR.tif",
        "result_RedEdge.tif", "result_Red.tif",
        "cloud_merged.las", "dem.tif", "dom.tif", "dsm.tif"
    ]
}

folders = [
    f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))
    ]

data = {
    folder: {
        os.path.join(sub, fname):
        os.path.exists(
            os.path.join(base_dir, folder, sub, fname.format(PLOT = folder))
            )
        for sub, fnames in files_to_check.items() for fname in fnames
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

for r in range(2, ws.max_row + 1):
    for c in range(2, ws.max_column + 1):
        cell = ws.cell(row = r, column = c)
        if cell.value is True:
            cell.fill = green
        elif cell.value is False:
            cell.fill = red

wb.save(excel_path)