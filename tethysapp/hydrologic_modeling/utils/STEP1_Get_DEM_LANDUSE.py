import arcpy

'''
Future Improvements:
Buffer distance and cell size meaningful values
'''


arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

inUsername = arcpy.GetParameterAsText(0)
inPassword = arcpy.GetParameterAsText(1)
outGDB = arcpy.GetParameterAsText(2)
wshedBoundary = arcpy.GetParameterAsText(3)
bufferDi= arcpy.GetParameterAsText(4)
outCS = arcpy.GetParameterAsText(5)


if outGDB == "":
    inUsername = "prasanna_usu"
    inPassword = "Hydrology12!@"
    outGDB = r"E:\Research Data\00 Red Butte Creek\RBC_3\New File Geodatabase.gdb"
    wshedBoundary = r"E:\Research Data\00 Red Butte Creek\RBC_3\RawFiles.gdb\RBC_Box"
    bufferDi = ""
    outCS = ""

def step1_get_dem_landuse(inUsername,inPassword,outGDB,wshedBoundary,bufferDi, outCS):
    """
    :param inUsername: ArcGIS online Username
    :param inPassword: ArcGIS online password
    :param outGDB: geodatabase (or directory) where the downlaoded files will be saved
    :param wshedBoundary: polygon shapefile for which the DEM and landuse will be donwloaded
    :param bufferDi: Buffer distance in meters to download DEM and landuse. Serves as factor of safety
    :return: downloads and saves the DEM and landuse rasters. Also, projects them to a UTM zone 12 (for now) CS
    """

    # defaulted, to make things easier
    if inUsername == "": inUsername = "prasanna_usu"
    if inPassword  == "": inPassword = "Hydrology12!@"
    if bufferDi == "":
        bufferDi = 100


    # Set workspace environment
    arcpy.env.workspace  = arcpy.env.scratchWorkspace = outGDB   # = arcpy.env.scratchWorkspace
    arcpy.env.overwriteOutput = True

    # If no projection defined, assume the area is in Northen Utah, i.e. UTM 12N
    if outCS == "":
        outCS = arcpy.SpatialReference("North America Albers Equal Area Conic") #arcpy.SpatialReference("WGS 1984 UTM Zone 12N")
    arcpy.env.outputCoordinateSystem = outCS
    arcpy.env.overwriteOutput = True

    arcpy.FeatureClassToFeatureClass_conversion(wshedBoundary, outGDB, "Boundary")
    arcpy.MakeFeatureLayer_management("Boundary", "Boundary")

    # Buffer
    arcpy.Buffer_analysis("Boundary", "Buffer", "%s Meters"%bufferDi, "FULL", "ROUND", "NONE", "", "PLANAR")

    # Connect to ArcGIS Servers
    out_folder_path = 'GIS Servers'

    out_landscape = 'Landscape.ags'
    server_landscape = 'https://landscape5.arcgis.com:443/arcgis/services/'

    out_elevation = 'Elevation.ags'
    server_elevation = 'https://elevation.arcgis.com:443/arcgis/services/'

    arcpy.mapping.CreateGISServerConnectionFile("USE_GIS_SERVICES",
                                                    out_folder_path,
                                                    out_landscape,
                                                    server_landscape,
                                                    "ARCGIS_SERVER",
                                                    username=inUsername,
                                                    password=inPassword,
                                                    save_username_password=True)

    arcpy.mapping.CreateGISServerConnectionFile("USE_GIS_SERVICES",
                                                    out_folder_path,
                                                    out_elevation,
                                                    server_elevation,
                                                    "ARCGIS_SERVER",
                                                    username=inUsername,
                                                    password=inPassword,
                                                    save_username_password=True)

    # Extract Image Server Data
    """ Land Use """
    NLCD_ImageServer = "GIS Servers\\Landscape\\USA_NLCD_2011.ImageServer"
    arcpy.MakeImageServerLayer_management(NLCD_ImageServer,"NLCD_Layer")
    arcpy.gp.ExtractByMask_sa("NLCD_Layer", "Buffer", "Land_Use")

    """ Percent Impervious """
    Imp_ImageServer = "GIS Servers\\Landscape\\USA_NLCD_Impervious_2011.ImageServer"
    arcpy.MakeImageServerLayer_management(Imp_ImageServer, "Impervious_Layer")
    arcpy.gp.ExtractByMask_sa("Impervious_Layer", "Buffer", "Impervious")

    # """ Soils HSG, USDA """
    # Soils_ImageServer = "GIS Servers\\Landscape\\USA_Soils_Hydrologic_Group.ImageServer"
    # arcpy.MakeImageServerLayer_management(Soils_ImageServer, "Soils_Layer")
    # arcpy.gp.ExtractByMask_sa("Soils_Layer", "Buffer", "SoilsHSG")

    """ DEM, 30m NED """
    NED30m_ImageServer = "GIS Servers\\Elevation\\NED30m.ImageServer"
    arcpy.MakeImageServerLayer_management(NED30m_ImageServer, "NED30m_Layer")
    arcpy.gp.ExtractByMask_sa("NED30m_Layer", "Buffer", "DEM")
    arcpy.AddMessage("DEM and Land Use data, i.e. NLCD , download complete")

    # Project the rasters
    arcpy.ProjectRaster_management(in_raster="DEM", out_raster="DEM_Prj", out_coor_system=outCS)
    arcpy.ProjectRaster_management(in_raster="Land_Use", out_raster="Land_Use_Prj", out_coor_system= outCS)

    arcpy.AddMessage("DEM and Land Use file projected")




if __name__ == "__main__":
    step1_get_dem_landuse(inUsername,inPassword,outGDB,wshedBoundary,bufferDi, outCS)




















# import arcpy
# import os
# import sys
# '''
#
# Future Improvements:
# Buffer distance and cell size meaningful values
# '''
#
#
# arcpy.env.overwriteOutput = True
# arcpy.CheckOutExtension("Spatial")
#
# inUsername = arcpy.GetParameterAsText(0)
# inPassword = arcpy.GetParameterAsText(1)
# outGDB = arcpy.GetParameterAsText(2)
# wshedBoundary = arcpy.GetParameterAsText(3)
# bufferDi= arcpy.GetParameterAsText(4)
# cell_size = arcpy.GetParameterAsText(5)
# outCS =  arcpy.GetParameterAsText(6)
#
#
# def step1_get_dem_landuse(inUsername,inPassword,outGDB,wshedBoundary,bufferDi,cell_size, outCS):
#     """
#     :param inUsername: ArcGIS online Username
#     :param inPassword: ArcGIS online password
#     :param outGDB: geodatabase (or directory) where the downlaoded files will be saved
#     :param wshedBoundary: polygon shapefile for which the DEM and landuse will be donwloaded
#     :param bufferDi: Buffer distance in meters to download DEM and landuse. Serves as factor of safety
#     :param cell_size: The resolution or the cell size. A float (or integer) number, e.g. 30 or 100 etc.
#     :return: downloads and saves the DEM and landuse rasters. Also, projects them to a UTM zone 12 (for now) CS
#     """
#
#     # defaulted, to make things easier
#     if inUsername == "": inUsername = "prasanna_usu"
#     if inPassword  == "": inPassword = "Hydrology12!@"
#     if bufferDi == "":
#         if cell_size == "":
#             bufferDi = 100
#         else:
#             bufferDi = float(cell_size) * 3
#
#     # Set workspace environment
#     arcpy.env.workspace  = outGDB   # = arcpy.env.scratchWorkspace
#
#     # If no projection defined, assume the area is in Northen Utah, i.e. UTM 12N
#     if outCS == "":
#         outCS = arcpy.SpatialReference("WGS 1984 UTM Zone 12N")
#     arcpy.env.outputCoordinateSystem = outCS
#     arcpy.env.overwriteOutput = True
#
#     # Connect to ArcGIS Servers
#     arcpy.mapping.CreateGISServerConnectionFile("USE_GIS_SERVICES",
#                                                     'GIS Servers',
#                                                     'Landscape.ags',
#                                                     'https://landscape5.arcgis.com:443/arcgis/services/',
#                                                     "ARCGIS_SERVER",
#                                                     username=inUsername,
#                                                     password=inPassword,
#                                                     save_username_password=True)
#
#     arcpy.mapping.CreateGISServerConnectionFile("USE_GIS_SERVICES",
#                                                     'GIS Servers',
#                                                     'Elevation.ags',
#                                                     'https://elevation.arcgis.com:443/arcgis/services/',
#                                                     "ARCGIS_SERVER",
#                                                     username=inUsername,
#                                                     password=inPassword,
#                                                     save_username_password=True)
#
#     # Extract Image Server Data
#     """ DEM, 30m NED """
#     NED30m_ImageServer = "GIS Servers\\Elevation\\NED30m.ImageServer"
#     arcpy.MakeImageServerLayer_management(NED30m_ImageServer, "NED30m_Layer")
#     arcpy.gp.ExtractByMask_sa("NED30m_Layer", wshedBoundary, os.path.join(outGDB,"DEM"))
#
#     arcpy.env.snapRaster = "DEM"                                              # Set Snap Raster environment
#
#     """ Land Use """
#     arcpy.MakeImageServerLayer_management("GIS Servers\\Landscape\\USA_NLCD_2011.ImageServer","NLCD_Layer")
#     arcpy.gp.ExtractByMask_sa("NLCD_Layer", os.path.join(outGDB,"DEM"), os.path.join(outGDB,"Land_Use"))
#
#     arcpy.AddMessage("DEM and Land Use data, i.e. NLCD , download complete")
#
#
#     # Project the rasters
#     arcpy.ProjectRaster_management(in_raster=os.path.join(outGDB,"DEM"), out_raster="DEM_Prj", out_coor_system=outCS)
#     arcpy.ProjectRaster_management(in_raster=os.path.join(outGDB,"Land_Use"), out_raster="Land_Use_Prj", out_coor_system= outCS)
#
#     arcpy.AddMessage("DEM and Land Use file projected")
#
#     #put DEM and Land_Use on maps as a layer
#     mxd = arcpy.mapping.MapDocument("CURRENT")                                  # get the map document
#     df = arcpy.mapping.ListDataFrames(mxd,"*")[0]                               #first dataframe in the document
#
#     #if cell size given, need to resample here
#     if cell_size != "":
#         """ resample to the user specified resolution """
#
#         arcpy.CopyRaster_management(in_raster="DEM_Prj",
#                                     out_rasterdataset="DEM_temp",
#                                     nodata_value="-9999")
#
#         arcpy.Resample_management(in_raster= "DEM_temp",
#                                   out_raster= "DEM_Prj",
#                                   cell_size= str(cell_size)+" "+str(cell_size), resampling_type="NEAREST")
#
#         arcpy.CopyRaster_management(in_raster="Land_Use_Prj",
#                                 out_rasterdataset="Landuse_temp",
#                                 nodata_value="-9999")
#         arcpy.Resample_management(in_raster= "Landuse_temp",
#                                   out_raster= "Land_Use_Prj",
#                                   cell_size=str(cell_size)+" "+str(cell_size), resampling_type="NEAREST")
#
#         arcpy.AddMessage("************Resample DEM and Land Use with cell size %s m completed ************"%cell_size)
#
#
#     DEM_layer = arcpy.mapping.Layer("DEM_Prj")    # create a new layer
#     arcpy.mapping.AddLayer(df, DEM_layer,"TOP")
#
#     LandUse_layer = arcpy.mapping.Layer("Land_Use_Prj")    # create a new layer
#     arcpy.mapping.AddLayer(df, LandUse_layer,"TOP")
#
#
# if __name__ == "__main__":
#     step1_get_dem_landuse(inUsername,inPassword,outGDB,wshedBoundary,bufferDi,cell_size, outCS)

