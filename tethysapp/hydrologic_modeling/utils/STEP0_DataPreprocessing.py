import os
from STEP1_Get_DEM_LANDUSE import step1_get_dem_landuse
from STEP2_DEM_Processing import step2_dem_processing
from STEP4_Join_Merge_Export import STEP4_Join_Merge_Export
import arcpy
from ConfigParser import SafeConfigParser
import shutil

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

# inputs, from ArcGIS toolbox
inUsername = arcpy.GetParameterAsText(0)
inPassword = arcpy.GetParameterAsText(1)
projDir = arcpy.GetParameterAsText(2)           # RAW FILES
wshedBoundary = arcpy.GetParameterAsText(3)     # Bounding Box, as layer
bufferDi= arcpy.GetParameterAsText(4)
cell_size = arcpy.GetParameterAsText(5)
outlet_fullpath = arcpy.GetParameterAsText(6)   # as layer again
areaThreshold = arcpy.GetParameterAsText(7)     # Threshold for defining stream in km2
path2ssurgoFolders = arcpy.GetParameterAsText(8)
path2statsgoFolders = arcpy.GetParameterAsText(9)
outCS = arcpy.GetParameterAsText(10)

# INPUTS, if script ran as standalone
if projDir == "":

    # initializing
    ini_fname = "./Onion_simulation.ini"
    config = SafeConfigParser()
    config.read(ini_fname)

    # path to directories
    path2ssurgoFolders = config.get('directory', 'ssurgo_collection')
    path2statsgoFolders = config.get('directory', 'statsgo_collection')
    projDir = config.get('directory', 'projDir')

    # path to shapefiles
    outlet_fullpath = config.get('input_files', 'outlet_fullpath')
    wshedBoundary = config.get('input_files', 'wshedBoundary')

    # path to other variables
    areaThreshold = config.get('other_parameter', 'areaThreshold')
    inUsername = config.get('other_parameter', 'inUsername')
    inPassword = config.get('other_parameter', 'inPassword')
    bufferDi = config.get('other_parameter', 'bufferDi')
    cell_size = config.get('other_parameter', 'cell_size')
    outCS = config.get('other_parameter', 'outCS')

    # output
    tiff_folder = config.get('output', 'tiff_folder')

    # flags, which help decide whether or no
    download_data = config.get('flags', 'download_data')
    process_dem = config.get('flags', 'process_dem')
    extract_ssurgo_data = config.get('flags', 'extract_ssurgo_data')
    merge_ssurgo_to_raster = config.get('flags', 'merge_ssurgo_to_raster')

    del_downloaded_files = config.get('flags', 'del_downloaded_files')
    del_ssurgo_files = config.get('flags', 'del_ssurgo_files')
    del_demProcessed_files = config.get('flags', 'del_demProcessed_files')


# list of empty directories to be made
folders_to_create = ['DEM_processed_rasters', 'SSURGO_rasters', 'TIFFS']

# Out Directories
raw_files_outDir = os.path.join(projDir, "Raw_files.gdb")
downloads_outDir = os.path.join(projDir, "Downloads.gdb")
DEM_processed_projDir = os.path.join(projDir, folders_to_create[0])
ssurgo_outDir = os.path.join(projDir,folders_to_create[1])
tiffs_outDir = os.path.join(projDir, folders_to_create[2])


# make the empty directories
try:
    for folder in folders_to_create:
        directory = os.path.join(projDir,folder)
        if not os.path.exists(directory):
            os.makedirs(directory)
        arcpy.CreateFileGDB_management(projDir, "Raw_files.gdb")
        arcpy.CreateFileGDB_management(projDir, "Downloads.gdb")

except Exception, e:
    arcpy.AddMessage(e)

arcpy.env.workspace = arcpy.env.scratchWorkspace = projDir

if download_data.lower() == 'true':
    # Step1, download the data
    step1_get_dem_landuse(inUsername,inPassword,downloads_outDir ,wshedBoundary,bufferDi, outCS)

if process_dem.lower() == 'true':
    # Step2
    DEM_fullpath = os.path.join(downloads_outDir, "DEM_Prj")
    land_use_fullpath = os.path.join(downloads_outDir, "Land_Use_Prj")

    if download_data.lower() == 'false':
        DEM_fullpath = os.path.join(downloads_outDir, "DEM")
        land_use_fullpath = os.path.join(downloads_outDir, "Land_Use")

    step2_dem_processing(DEM_fullpath, land_use_fullpath ,raw_files_outDir , outlet_fullpath, areaThreshold,cell_size, outCS)

if extract_ssurgo_data.lower() == 'true':
    # Step3
    try:
        from STEP3_Merge_SSURGO import step3_merge_ssurgo
        lookupTable = os.path.join(os.getcwd(), "GREENAMPT_LOOKUPTABLE.csv")
        step3_merge_ssurgo(path2ssurgoFolders ,path2lookupTable=lookupTable )
        step3_merge_ssurgo(path2statsgoFolders ,path2lookupTable=lookupTable )
    except Exception,e:
        arcpy.AddMessage(e)

if merge_ssurgo_to_raster.lower() == 'true':
    # Step4
    MatchRaster = os.path.join(raw_files_outDir, "mask_r")
    STEP4_Join_Merge_Export (path2ssurgoFolders, path2statsgoFolders, ssurgo_outDir, MatchRaster )

# To tif, and flt
for outRaster in ["mask_r", "DEM_Prj_fc",  "n_Overland", "n_Channel", "fdr_cr" , "slope_c", "SD", "str_c", "str_cr9999", "str_cr255"]:
    arcpy.RasterToOtherFormat_conversion(Input_Rasters="'%s'"%(os.path.join(raw_files_outDir, outRaster)), Output_Workspace=tiffs_outDir, Raster_Format="TIFF")

for outRaster in ["bbl-tc.tif", "efpo-tc.tif", "ksat-tc.tif",  "psd-tc.tif", "por-tc.tif", "rsm-tc.tif" , "SD-sc.tif","AWC-sc.tif"]:
    arcpy.RasterToOtherFormat_conversion(Input_Rasters="'%s'"%(os.path.join(ssurgo_outDir, outRaster)), Output_Workspace=tiffs_outDir, Raster_Format="TIFF")

# delete unnecessary files
# unnecessary files in TIF folder, that are not tif
for file in os.listdir(tiffs_outDir):
    if not file.split(".")[-1] in ['tif', "gdb", "xlsx"] :
        os.remove(os.path.join(tiffs_outDir,file))
for file in os.listdir(ssurgo_outDir):
    if file.split(".")[-1] in ['tif' , 'TEMP']:
        os.remove(os.path.join(ssurgo_outDir,file))

# copy files
try:
    # tif_folder = folder where tiff are supposed to be saved for pytopkapi
    # tif_outDir = folder where tiff are created by the script above
    if not os.path.exists(tiff_folder):
        os.mkdir(tiff_folder)
    for file in os.listdir(tiffs_outDir):
        shutil.copy(os.path.join(tiffs_outDir,file), tiff_folder)

    # del downloaded files
    if del_downloaded_files.lower()== 'true':
        shutil.rmtree(downloads_outDir, ignore_errors=True)
        # for file in os.listdir(downloads_outDir):
        #     os.remove(os.path.join(downloads_outDir, file))
        # os.rmdir(downloads_outDir)

    # del DEM processed file
    if del_ssurgo_files.lower()== 'true':
        shutil.rmtree(raw_files_outDir, ignore_errors=True)

    # del SSURGO files
    if del_demProcessed_files.lower()== 'true':
        shutil.rmtree(ssurgo_outDir, ignore_errors=True)
except Exception, e:
    arcpy.AddMessage( "FAILURE: Deleting temporary files. Error: %s"%e)

