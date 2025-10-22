Insights

## Flight altitudes
DJI uses ellipsoidal flight altitudes. Hence, when providing a flight altitude, we must translate it to ellipsoidal height. However, when DJI is provided with a DEM and an altitude above ground, the DEM must be relative to the EGM96 geoid model. DJI Pilot 2 apparently does the conversion by itself.

The default DEM the DJI Pilot 2 app uses is the ASTER GDEM V3. However, a comparison between this DTM and the SwissALTI3D shows significant differences (within a $1 \times 1$ km test area, differences ranged from -12 to +26 m with a standard deviation of 6.3).