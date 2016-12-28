import arcpy
from arcpy.sa import *
import os
'''
I/O
--------------------------
Input:  DEM and NLCD landuse raster
        Watershed outlet point, saving directory, threshold no. for defining stream
Output:
        Rasters: Slope, Fdr, Fac, Stream, Catchments, Watershed, Mannings n for overland & channel
        Vector:  Catchment/sub-watershed, streamnet

ISSUES:
---------------------------
If output is folder, dissolve (around line 77 ) does not work

IMPROVEMENTS
---------------------------
1.Soil depth is in string
2.Land use reclassification from the file
3.soil depth still missing
4.Mask is created after delineating wshed from Outlet created in SnapPourPoint process. BUT,
    the outlet raster created takes its value from a field in vector point outlet shapefile as user input
    if the file does not have 1, the mask will end up with value != 1. Therefore,
    for user input outlet, need to add field and assign value =1
5.Threshold should also be such that the area draining = 25 km2
6.Cell without stream reclassified to 255. This done aiming Pytopkapi, for other it might need correction
'''



DEM_fullpath = arcpy.GetParameterAsText(0)             # raster layer
land_use_fullpath = arcpy.GetParameterAsText(1)        # raster layer
outDir= arcpy.GetParameterAsText(2)
outlet_fullpath = arcpy.GetParameterAsText(3)          # feature layer
area_threshold = arcpy.GetParameterAsText(4)
cell_size = arcpy.GetParameterAsText(5)
outCS = arcpy.GetParameterAsText(6)

if DEM_fullpath == "":
    # inputs for standalone operation
    DEM_fullpath = r"E:\Research Data\del\Downloads.gdb\DEM_Prj"
    land_use_fullpath = r"E:\Research Data\del\Downloads.gdb\LU_Prj"
    outDir= r"E:\Research Data\del\New File Geodatabase.gdb"
    outlet_fullpath = r"E:\Research Data\00 Red Butte Creek\RBC_point_Area\RawFiles.gdb\RBC_outlet"
    area_threshold = ""
    cell_size = ""
    outCS = ""

def step2_dem_processing(DEM_fullpath, land_use_fullpath, outDir, outlet_fullpath, area_threshold, cell_size, outCS):
    """
    :param DEM: Projected DEM (for now, projected to UTM zone 12)
    :param land_use: Projected Land_use raster from NLCD
    :param outDir: geodatabase where the rasters created are stored
    :param outlet_point_sf: the point shapefile for the outlet point
    :param area_threshold: Area of Threshold for defining stream in km2
    :return:
    """
    arcpy.AddMessage("*** This scripts Processes the DEM and Landuse data *** ")
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("Spatial")  # turns on spatial extension, required if run as standalone script
    arcpy.env.workspace = outDir


    # If no projection defined
    if outCS == "":
        outCS =  arcpy.SpatialReference("North America Albers Equal Area Conic")
    arcpy.env.outputCoordinateSystem = outCS

    # make feature layer
    outlet_point_sf = os.path.basename(outlet_fullpath)
    print os.getcwd()
    arcpy.MakeFeatureLayer_management(outlet_fullpath,outlet_point_sf)

        # newly added
    # if cell size given, need to resample here
    if cell_size != "":
        """ resample to the user specified resolution """

        # arcpy.ProjectRaster_management(in_raster=DEM_fullpath,
        #                                out_raster=outDir+"/DEM_Prj",
        #                                out_coor_system= outCS ,
        #                                resampling_type="NEAREST", cell_size="%s %s"%(cell_size, cell_size), geographic_transform="",
        #                                Registration_Point="",
        #                                in_coor_system = "")
        #
        #
        # arcpy.ProjectRaster_management(in_raster=land_use_fullpath,
        #                                out_raster=outDir+"/LU_Prj",
        #                                out_coor_system=outCS,
        #                                resampling_type="NEAREST", cell_size="%s %s" % (cell_size, cell_size),
        #                                geographic_transform="",
        #                                Registration_Point="",
        #                                in_coor_system="")

        # arcpy.ProjectRaster_management(in_raster=DEM_fullpath, out_raster="DEM_temp", out_coor_system=outCS)
        arcpy.Resample_management(in_raster= DEM_fullpath,
                                  out_raster= "DEM_Prj",
                                  cell_size= str(cell_size)+" "+str(cell_size), resampling_type="NEAREST")


        # arcpy.ProjectRaster_management(in_raster=land_use_fullpath, out_raster="Landuse_temp", out_coor_system=outCS)
        arcpy.Resample_management(in_raster= land_use_fullpath,
                                  out_raster= "LU_Prj",
                                  cell_size=str(cell_size)+" "+str(cell_size), resampling_type="NEAREST")


        DEM_fullpath = os.path.join(outDir , "DEM_Prj")
        land_use_fullpath= os.path.join(outDir , "LU_Prj")

        arcpy.AddMessage("SUCCESS: Resampling DEM and Land Use with cell size %s "%cell_size)



    arcpy.MakeRasterLayer_management(DEM_fullpath, "DEM_lyr",  "#", "", "1")
    arcpy.MakeRasterLayer_management(land_use_fullpath, "LU_lyr",  "#", "", "1")

    # Set workspace environment, and some defaults
    arcpy.env.snapRaster = DEM_fullpath           # Set Snap Raster environment

    cellSize = arcpy.Describe("DEM_lyr").children[0].meanCellHeight

    # set default threshold value for stream definition
    if area_threshold == "": # threshold = "3000"
        area_threshold = 1 #km2
    threshold = int (float(area_threshold) / ( (cellSize)/1000. )**2)

    # DEM processing: Fill> fdr> fac> slope> stream> watershed
    Fill("DEM_lyr").save("fel")
    FlowDirection("fel").save('fdr')
    FlowAccumulation('fdr').save('fac')
    Slope("fel", "DEGREE", "1").save('slope')
    # FlowDirection("fel", "NORMAL",'slope').save('fdr')
    SnapPourPoint(outlet_point_sf, 'fac', 5* cellSize,"").save("Outlet")  # snaps to str if outlet point around 5 cell
    Watershed('fdr', "Outlet", "Count").save("mask")
    StreamRaster = (Raster('fac') >= float(threshold)) & (Raster("mask") >= 0) ; StreamRaster.save('str')

    try:
        # Added code
        outStreamLink = StreamLink('str','fdr') ; outStreamLink.save('strlnk')
        Catchment = Watershed('fdr', 'strlnk'); Catchment.save("catchment")            # no need catchment, mask is good
        StreamToFeature('strlnk', 'fdr', "Streamnet","NO_SIMPLIFY")                    # stream defined
        arcpy.RasterToPolygon_conversion("catchment", "CatchTemp", "NO_SIMPLIFY")
        arcpy.Dissolve_management("catchtemp", "CatchPoly", "GRIDCODE")                # dissolves extra catchments
        # arcpy.Dissolve_management(in_features="catchtemp", out_feature_class="CatchPoly.shp", dissolve_field="GRIDCODE", statistics_fields="", multi_part="MULTI_PART", unsplit_lines="DISSOLVE_LINES")

    except Exception, e:
        arcpy.AddMessage("FAILURE: Creation of sub catchments")

    arcpy.AddMessage("SUCCESS: Fdr, Fac, Stream processing complete ")


    # # clip to the mask--------------------------------------------------------
    ExtractByMask('str', "mask").save('str_c')
    ExtractByMask('fdr', "mask").save("fdr_c")
    ExtractByMask("slope", "mask").save("slope_c")
    ExtractByMask("fel", "mask").save("DEM_Prj_fc")      # f for fill, c for clip

    # for some reason there is problem once in a while in this step
    # ExtractByMask( 'LU_lyr', "mask").save("NLCD_c")
    arcpy.gp.ExtractByMask_sa(
        outDir+"/LU_Prj",
        outDir+"/mask",
        outDir+"/NLCD_c")

    #strahler for mannings for channel
    arcpy.gp.StreamOrder_sa("str_c", "fdr_c", "STRAHLER", "STRAHLER")  # the last parameter, Strahler string, is actually a method of ordering stream. NOT A NAME
    arcpy.AddMessage("SUCCESS: Strahler stream order processing complete")

    # arcpy.AddField_management(in_table= "NLCD_c" , field_name="ManningsN", field_type="LONG",field_precision="",
    #                           field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE",
    #                           field_is_required="NON_REQUIRED", field_domain="")
    arcpy.AddMessage("SUCCESS: Adding field to Land Use complete")

    # multiply Manning's n by 10,000. We will later divide it by 10,000 again
    arcpy.gp.Reclassify_sa("NLCD_c", "Value", "11 0;21 404;22 678;23 678;24 404;31 113;41 3600;42 3200;43 4000;52 4000;71 3680;81 3250;82 3250;90 860;95 1825", outDir+"/nx10000_Overl", "DATA")
    arcpy.AddMessage("SUCCESS: Land Use reclassification to obtain Mannings n complete ")

    # reclassifying Strahler order to get Manning's for channel in the same way
    arcpy.gp.Reclassify_sa("STRAHLER", "Value", "1 500;2 400;3 350;4 300;5 300;6 250;NODATA 0", outDir+"/nx10000_Chan", "DATA")
    arcpy.AddMessage("SUCCESS: Strahler order raster reclassification to obtain Mannings n complete **********")

    # now, NLCD to n calculate the real Manning's, divide reclassified raster by 10,000
    arcpy.gp.RasterCalculator_sa(""""nx10000_Overl" /10000.0""", outDir+"/n_Overland")
    arcpy.gp.RasterCalculator_sa(""""nx10000_Chan" /10000.0""", outDir+"/n_Channel")

    # reclassify and clip peformed in n_channel to obtain 0 values for watershed cells which is not stream
    # arcpy.gp.Reclassify_sa("n_Channel", "Value", "1 1;2 2;3 3;4 4;5 5;6 6;NODATA 0", "n_Channel_r", "DATA")
    ExtractByMask("n_Channel", "mask").save('n_Channel_c')

    arcpy.AddMessage("SUCCESS: All of DEM processing complete ")

    # Reclassify to change no data to -9999
    arcpy.gp.Reclassify_sa("fdr_c", "Value", "1 1;2 2;4 4;8 8;16 16;32 32;64 64;128 128;NODATA -9999", "fdr_cr", "DATA")
    arcpy.gp.Reclassify_sa("str_c", "Value", "0 255;1 1;NODATA 255", "str_cr255", "DATA") #arcpy.gp.Reclassify_sa(str, "Value", "0 0;1 1;NODATA -9999", str + "_r", "DATA")
    arcpy.gp.Reclassify_sa("str_c", "Value", "0 0;1 1;NODATA -9999", "str_cr9999", "DATA")
    arcpy.gp.Reclassify_sa("mask", "Value", "2 1", "mask_r", "DATA")

    arcpy.CopyRaster_management(in_raster="mask_r",out_rasterdataset="SD",nodata_value="-9999")
    arcpy.AddMessage("SUCCESS: Assigning -9999 to NoData, mask and Soil depth creation  completed")


    try:
        # Add n_Channel and n_Overland to layer and then to map document
        mxd = arcpy.mapping.MapDocument("CURRENT")                      # get the map document
        df = arcpy.mapping.ListDataFrames(mxd,"*")[0]                   # first data-frame in the document

        fdr_layer = arcpy.mapping.Layer(outDir+"/"+ "mask_r")                 # create a new layer
        arcpy.mapping.AddLayer(df, fdr_layer ,"TOP")

        dem_layer = arcpy.mapping.Layer(outDir+"/"+ "DEM_Prj_fc" )                 # create a new layer
        arcpy.mapping.AddLayer(df, dem_layer ,"TOP")

        str_layer = arcpy.mapping.Layer(outDir+"/"+ "str_cr" )                 # create a new layer
        arcpy.mapping.AddLayer(df, str_layer ,"TOP")

        landuse_layer = arcpy.mapping.Layer(outDir+"/"+ "NLCD_c" )                 # create a new layer
        arcpy.mapping.AddLayer(df, landuse_layer ,"TOP")

        # n_Channel_layer = arcpy.mapping.Layer(outDir+"/n_Channel")      # create a new layer
        # arcpy.mapping.AddLayer(df, n_Channel_layer ,"TOP")

        n_Overland_layer = arcpy.mapping.Layer(outDir+"/n_Overland")    # create a new layer
        arcpy.mapping.AddLayer(df, n_Overland_layer,"TOP")

        fdr_layer = arcpy.mapping.Layer(outDir+"/"+"fdr_cr")                 # create a new layer
        arcpy.mapping.AddLayer(df, fdr_layer ,"TOP")

        slope_layer = arcpy.mapping.Layer(outDir+"/"+ "slope_c")                # create a new layer
        arcpy.mapping.AddLayer(df, slope_layer ,"TOP")


    except Exception, e:
        print(arcpy.GetMessages())
if __name__ == "__main__":
    step2_dem_processing(DEM_fullpath, land_use_fullpath, outDir, outlet_fullpath, area_threshold, cell_size, outCS)

