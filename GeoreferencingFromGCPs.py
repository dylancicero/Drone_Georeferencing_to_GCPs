# Import external modules
import sys, os, string, math, arcpy, traceback, numpy
from arcpy import env
from arcpy.sa import *

# If Spatial Analyst license is available, check it out
if arcpy.CheckExtension("spatial") == "Available":
    arcpy.CheckOutExtension("spatial")

    
    try:
        # Accept grids from user-inputted parameters
        InputGridRed = arcpy.GetParameterAsText(0)
        InputGridGreen = arcpy.GetParameterAsText(1)
        InputGridBlue = arcpy.GetParameterAsText(2)

        
        # Reclassify input grid so to convert NoData values into highest value real pixels
        # The white pixels of the GCPs saturated the camera sensors during the mission
        ReclassedRed = Reclassify(InputGridRed, "Value", RemapValue([["NODATA",255]]))
        ReclassedGreen = Reclassify(InputGridGreen, "Value", RemapValue([["NODATA",255]]))
        ReclassedBlue = Reclassify(InputGridBlue, "Value", RemapValue([["NODATA",255]]))

        
        # Stack bands to form single composite raster
        arcpy.env.workspace = "C:\Users\dfc24\Documents\ArcGIS\Default.gdb"
        arcpy.CompositeBands_management([ReclassedRed, ReclassedGreen, ReclassedBlue], "Comp")

        
        # Classify the raster using the isodata unsupervised classification algorithm
        arcpy.AddMessage("Training Classifier")
        TrainIsoClusterClassifier("Comp",10,"U:\Geospatial_Software_Final_Projects\ArcPy_Georeferencing\ClassDef.ecd","#",20,20,1)
        Classified = ClassifyRaster("Comp", "U:\Geospatial_Software_Final_Projects\ArcPy_Georeferencing\ClassDef.ecd")

        
        # Reclassify raster in order to recieve a count of pixels in each class
        ReclassForCount = Reclassify(Classified, "Value", RemapValue([[0,0]]))

        
        # Select all pixels in class with fewest pixels and export only those pixels to a new raster layer
        # Sort the attribute table on the basis of the pixel count
        attributeTable = arcpy.SearchCursor(ReclassForCount)
        Count = 1000000000000
        for nextRecord in attributeTable:
            Count1 = nextRecord.getValue("Count")
            arcpy.AddMessage(str(Count))
            arcpy.AddMessage(str(Count1))
            if Count1 < Count:
                Count = Count1
        arcpy.MakeRasterLayer_management(ReclassForCount,"ReclassForCountlyr")
        selectionQuery =  '"' + "Count" + '"' + " = " + str(Count)
        arcpy.SelectLayerByAttribute_management("ReclassForCountlyr","NEW_SELECTION")
        arcpy.MakeRasterLayer_management("ReclassForCountlyr", "FewestPixels", selectionQuery)
        arcpy.CopyRaster_management("FewestPixels","FewestPixelsDataset")

        
        # Convert the selected pixels of the classified grid into polygons based on class
        # The output grid will be complete with "Shape_Length" and "Shape_Area" attributes, expiditing the next step
        arcpy.RasterToPolygon_conversion("FewestPixels", "Polygons", "SIMPLIFY", "Value", "SINGLE_OUTER_PART")

        
        # Add a new "area" field.  This "area" field will be tranposed into the attribute table of the feature class that results from upcoming "buffer" operation
        # This step is necessary becuase the "Shape_Area" field is not carried over into the buffered feature class (for one reason or the other).
        # 1) Add field for area
        arcpy.AddField_management("Polygons", "AreaMGCP", "FLOAT")
        # 2) Calculate fields
        arcpy.CalculateField_management("Polygons", "AreaMGCP","abs([Shape_Area] - .2025)", "VB")

        
        # Select only polygons that are within a 'reasonable' range of the true size of the GCPs (Each GCP is .45cm^2 = .2025m^2).
        # 'Reasonable' range defined here as within .12m^2
        # Create a new set of polygons out of those selected
        # This step is solely for efficiency... here we remove thousands of polygons that are irrelevant prior to a costly buffer step.
        Field = "AreaMGCP"
        selectionQuery =  '"' + Field + '"' + ' <= .12'
        arcpy.AddMessage(selectionQuery)
        arcpy.MakeFeatureLayer_management("Polygons", "Polygons_Focused", selectionQuery)
        

        # Buffer the "polygons" feature class inward so that any protruding pixels that have been classified as part of the square GCP are removed.
        arcpy.AddMessage("Buffering Inward")
        arcpy.Buffer_analysis("Polygons_Focused","Buffered_Inward", -0.1, "#","FLAT")

        
        # Sort the buffered attribute table on the basis of the difference from the true size of the GCPs
        arcpy.Sort_management("Buffered_Inward", "Sorted", [["AreaMGCP", "Descending"]])
        
        
        # Extract n largest polygons from sorted attribute table, where n is a user-defined number of GCPs to georeference.
        Field = "OBJECTID"
        UpperBounds = arcpy.GetParameterAsText(3)
        # selectionQuery =  '"' + Field + " > 10" +'"'
        selectionQuery =  '"' + Field + '"' + ' > 0 AND ' + '"' + Field + '"' + ' <= ' + UpperBounds
        arcpy.AddMessage(selectionQuery)
        arcpy.MakeFeatureLayer_management("Sorted", "GCPLayer", selectionQuery)
        arcpy.CopyFeatures_management("GCPLayer", "GCPs")

        
        # Determine the centroid for each GCP
        arcpy.FeatureToPoint_management("GCPs", "Centroids")

        
        # Add XY Coordinates to the GCPs
        targetPoints = arcpy.GetParameterAsText(4)
        spatial_ref = arcpy.Describe(targetPoints).spatialReference
        arcpy.env.outputCoordinateSystem = spatial_ref
        arcpy.AddXY_management("Centroids")
        

        # Use a spatial join to match each GCP centroid with its nearest source point
        arcpy.SpatialJoin_analysis(targetPoints, "Centroids", "Joined", "#", "KEEP_COMMON", "#", "CLOSEST")

        
        # Iterate through the attribute table to create a list of source control points and target control points.
        attributeTable = arcpy.UpdateCursor("Joined")
        target_points = ""
        source_points = ""
        GCP_list = []
        longitude_field = arcpy.GetParameterAsText(5)
        latitude_field = arcpy.GetParameterAsText(6)

        for nextRecord in attributeTable:
            TargetX = nextRecord.getValue(longitude_field)
            TargetY = nextRecord.getValue(latitude_field)
            GCPX = nextRecord.getValue("Point_X")
            GCPY = nextRecord.getValue("Point_Y")
            target_points = target_points + ";'" + str(TargetX) + " " + str(TargetY) + "'"
            source_points = source_points + ";'" + str(GCPX) + " " + str(GCPY) + "'"

        arcpy.AddMessage(target_points)
        arcpy.AddMessage(source_points)


        # Use the ordered lists of points as input to the warp method for georeferencing
        savedLocation = arcpy.GetParameterAsText(7)
        # arcpy.MakeRasterLayer_management("Composite", "Composite_lyr")
        arcpy.Warp_management(InputGridRed, source_points, target_points, "Red")
        arcpy.Warp_management(InputGridGreen, source_points, target_points, "Green")
        arcpy.Warp_management(InputGridBlue, source_points, target_points, "Blue")

        
        # Composite georeferenced bands
        arcpy.CompositeBands_management(["Red", "Green", "Blue"], savedLocation)

         
    except Exception as e:
        # If unsuccessful, end gracefully by indicating why
        arcpy.AddError('\n' + "Script failed because: \t\t" + e.message )
        # ... and where
        exceptionreport = sys.exc_info()[2]
        fullermessage   = traceback.format_tb(exceptionreport)[0]
        arcpy.AddError("at this location: \n\n" + fullermessage + "\n")
        
        # Check in Spatial Analyst extension license
        arcpy.CheckInExtension("spatial")      
    else:
        print "Spatial Analyst license is " + arcpy.CheckExtension("spatial")
