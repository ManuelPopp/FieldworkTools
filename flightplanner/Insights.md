# Insights

## Flight altitudes
DJI uses ellipsoidal flight altitudes. Hence, when providing a flight altitude, we must translate it to ellipsoidal height. However, when DJI is provided with a DEM and an altitude above ground, the DEM must be relative to the EGM96 geoid model. DJI Pilot 2 apparently does the conversion by itself.

The default DEM the DJI Pilot 2 app uses is the ASTER GDEM V3. However, a comparison between this DTM and the SwissALTI3D shows significant differences (within a $1 \times 1$ km test area, differences ranged from -12 to +26 m with a standard deviation of 6.3). Visual inspection on site indicated that the ASTER GDEM has difficulties subtracting height of trees and similar landscape elements and, thus, overestimates terrain elevation under dense vegetation. Underestimation was common in the surroundings of buildings.

## Pre-flight checklist
When relying on DTM-based altitudes, check before each flight:
 - Does the UAV altitude before take-off matches the expected elevation based on the DTM?
 - Do the altitudes shown in the flightplanner plot seem reasonable, given the local terrain? Are artefacts visible in the DTM?