# An Automated Process for Georeferencing Drone Imagery to Ground Control Points

This project presents an ArcPy script which georeferences drone imagery to ground control points based on an 
unsupervised classification technique and other spatial data processing.

![tooldemo](https://user-images.githubusercontent.com/43111524/50660810-0cad9600-0f6f-11e9-8df0-7a80c6b836ea.png)
*(See pdf in repo to download and enlarge demo)*


## Getting Started

To use this script, a user first must create an ArcToolbox in ArcMap or ArcPro via the following steps:

1.   In  ArcMap > Catalog > Toolboxes > My Toolboxes, either select an existing toolbox
or right-click on My Toolboxes and use New > Toolbox to create (then rename) a new one.
2.   Drag (or use ArcToolbox > Add Toolbox to add) this toolbox to ArcToolbox.
3.   Right-click on the toolbox in ArcToolbox, and use Add > Script to open a dialog box.
4.   In this Add Script dialog box, use Label to name the tool being created, and press Next.
5.   In a new dialog box, browse to the .py file to be invoked by this tool, and press Next.
6.   In the next dialog box, specify the following inputs (using dropdown menus wherever possible)
before pressing OK or Finish.

```
DISPLAY NAME                    DATA TYPE           DIRECTION    DEFAULT
Input Band 1                    Raster Layer         Input
Input Band 2                    Raster Layer         Input
Input Band 3                    Raster Layer         Input
Number GCPs                     Long                 Input        3
Target Control Points           Feature Layer        Input
Target Longitude Field          Field                Input
Target Latitude Field           Field                Input
Output Grid                     Raster Dataset       Output
```

## Running

Run the script by double-clicking on the newly created Arctoolbox and inputting the appropriate parameters.
Included in this repository is an example drone image (3 bands) and a shapefile of GCP coordinates for georeferencing.
These may be used to trial the script.


## Acknowledgments

Inspired by Thomasson et al. 2017:

J. Alex  Thomasson, Yeyin  Shi, Chao  Sima, Chenghai  Yang, Dale A. Cope,"Automated geographic registration and radiometric correction for UAV-basedmosaics," Proc. SPIE 10218, Autonomous Air and Ground Sensing Systemsfor Agricultural Optimization and Phenotyping II, 102180K (16 May 2017); doi:10.1117/12.2263512

