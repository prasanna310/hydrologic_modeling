from datetime import datetime
import subprocess, shlex
import fiona

import os, sys

try:
    from osgeo import ogr, osr
except Exception, e:
    print e

from datetime import date, datetime



from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_gizmos.gizmo_options import MapView, MVLayer, MVView
from tethys_gizmos.gizmo_options import TextInput, DatePicker
from tethys_sdk.gizmos import TimeSeries
from tethys_sdk.gizmos import SelectInput




import sys
sys.path.append('/utils')
from utils.pytopkapi_utils import *




def create_hydrograph(date_in_datetime, Qsim, simulation_name, error):
    # preparing timeseries data in the format shown in: http://docs.tethysplatform.org/en/latest/tethys_sdk/gizmos/plot_view.html#time-series
    from tethys_sdk.gizmos import TimeSeries

    hydrograph = []
    date_broken = [[dt.year, dt.month, dt.day, dt.hour, dt.minute] for dt in date_in_datetime]
    for i in range(len(Qsim)):
        date = datetime(year=date_broken[i][0], month=date_broken[i][1], day=date_broken[i][2], hour=date_broken[i][3],
                        minute=date_broken[i][4])
        hydrograph.append([date, float(Qsim[i])])

    observed_hydrograph = TimeSeries(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Hydrograph ',
        subtitle="Simulated and Observed flow for " + simulation_name,
        y_axis_title='Discharge',
        y_axis_units='cumecs',
        series=[{
            'name': 'Simulated Flow',
            'data': hydrograph,
        }]
    )
    return observed_hydrograph

def create_model_input_dict_from_request(request):
    # from the user input forms in model_input page, the request is converted to a dictionary of inputs

    inputs_dictionary = {"user_name": request.user.username,
                         "simulation_name": request.POST['simulation_name'],
                         "simulation_start_date": request.POST['simulation_start_date_picker'],
                         "simulation_end_date": request.POST['simulation_end_date_picker'],
                         "USGS_gage": int(request.POST['USGS_gage']),

                         "outlet_y": float(request.POST['outlet_y']),
                         "outlet_x": float(request.POST['outlet_x']),
                         "box_topY": float(request.POST['box_topY']),
                         "box_bottomY": float(request.POST['box_bottomY']),
                         "box_rightX": float(request.POST['box_rightX']),
                         "box_leftX": float(request.POST['box_leftX']),

                         "timeseries_source": request.POST['timeseries_source'],

                         "threshold": int(request.POST['threshold']),
                         "cell_size": float(request.POST['cell_size']),
                         "timestep": float(request.POST['timestep']),
                         "model_engine": request.POST['model_engine'],

                         }
    return inputs_dictionary

def create_model_input_dict_from_db(current_model_inputs_table_id, user_name ):
    """
    :param model_inputs_table:  primary key id for the model_input table
    :param user_name:           tethys or hydroshare username
    :return:                    dictionary of input parameters
    """
    from .model import  SessionMaker, model_inputs_table
    from sqlalchemy import and_
    session = SessionMaker()

    # # IMPORTENT STEP: retrieve the model_inputs_table.id of this entry to pass it to the next page (calibration page)
    # current_model_inputs_table_id = str(len(session.query(model_inputs_table).filter(
    #     model_inputs_table.user_name == user_name).all()))  # because PK is the same as no of rows, i.e. length
    # print 'model_input ID for last sim, which will be used for calibration: ', current_model_inputs_table_id

    # # If passing to calibration is not our aim, we take the id as user input
    print 'MSG: model_input ID for which rest of the inputs are being retrieved: ', current_model_inputs_table_id

    # :TODO for a particular user_name also requird. Can be poorly achieved by writing if-clause in for-loop below
    all_rows = session.query(model_inputs_table).\
        filter(and_(model_inputs_table.id == current_model_inputs_table_id, model_inputs_table.user_name == user_name)).all()

    # retrieve the parameters and write to a dictionary
    inputs_dictionary = {}

    for row in all_rows:
        inputs_dictionary['id'] = row.id
        inputs_dictionary['user_name'] = row.user_name
        inputs_dictionary['simulation_name'] = row.simulation_name
        inputs_dictionary['simulation_folder'] = row.simulation_folder
        inputs_dictionary['simulation_start_date'] = row.simulation_start_date
        inputs_dictionary['simulation_end_date'] = row.simulation_end_date
        inputs_dictionary['USGS_gage'] = row.USGS_gage

        inputs_dictionary['outlet_x'] = row.outlet_x
        inputs_dictionary['outlet_y'] = row.outlet_y
        inputs_dictionary['box_topY'] = row.box_topY
        inputs_dictionary['box_bottomY'] = row.box_bottomY
        inputs_dictionary['box_rightX'] = row.box_rightX
        inputs_dictionary['box_leftX'] = row.box_leftX

        timeseries_source, threshold, cell_size, timestep = row.other_model_parameters.split("__")
        inputs_dictionary['timeseries_source'] = timeseries_source
        inputs_dictionary['threshold'] = threshold
        inputs_dictionary['cell_size'] = cell_size
        inputs_dictionary['timestep'] = timestep

        inputs_dictionary['model_engine'] = row.model_engine


    print 'MSG: SUCCESS Querrying the database to create dictionary '
    if inputs_dictionary == {}:
        print "MSG: ERROR, Dictionary Empty!!! "

    return  inputs_dictionary

def create_simulation_list_after_querying_db(user_name):
    # returns a tethys gizmo or a drop down list, which should be referenced in html with name = 'simulation_names_list'
    from .model import engine, SessionMaker, Base, model_inputs_table, model_calibration_table
    from tethys_sdk.gizmos import SelectInput

    Base.metadata.create_all(engine)    # Create tables
    session = SessionMaker()            # Make session

    # Query DB for gage objects
    simulations_queried = session.query(model_inputs_table).filter(model_inputs_table.user_name==user_name).all() # searches just the id input in URL

    simulation_names_list_queried = []
    simulation_names_id = []

    for row in simulations_queried:
        simulation_names_list_queried.append(row.simulation_name)
        simulation_names_id.append(row.id)

    queries = zip(simulation_names_list_queried,simulation_names_id )

    simulation_names_list = SelectInput(display_text='Saved Models',
                                     name='simulation_names_list',
                                     multiple=False,
                                     options= queries  #[ (  simulations_queried[0].id, '1'),  (  simulations_queried[1].simulation_name, '2'  ),  (   simulations_queried[1].user_name, '2'  )]
                                                          )
    return simulation_names_list

def get_outlet_xy_from_shp_shx(shp_file, shx_file, simulation_folder='/usr/lib/tethys/src/tethys_apps/tethysapp/my_first_app/workspaces/user_workspaces/usr1/'):
    from shapely.geometry import shape
    # convert the django_memory_file format to original shapefile
    filename = "outlet.shp"  # received file name
    file_obj = shp_file
    with open(simulation_folder +'/' + filename, 'w') as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)
    shp_file = simulation_folder +'/' + filename

    # convert the django_memory_file format to original shapefile
    filename = "outlet.shx"  # received file name
    file_obj = shx_file
    with open(simulation_folder +'/' + filename, 'w') as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)
    shx_file = simulation_folder +'/' + filename

    # use fiona to get the bounds
    c = fiona.open(shp_file)

    outlet_x = c.bounds[0]
    outlet_y = c.bounds[1]

    # # ----------- projection --------------------

    # driver = ogr.GetDriverByName('ESRI Shapefile')
    # dataSource = driver.Open(shp_file, 0)  # 0 means read-only, 1 means writeable
    # layer = dataSource.GetLayer()
    # sourceprj = layer.GetSpatialRef()
    # targetprj = osr.SpatialReference()
    # targetprj.ImportFromEPSG(4326)
    # transform = osr.CoordinateTransformation(sourceprj, targetprj)
    #
    # if sourceprj != None:
    #     point = ogr.CreateGeometryFromWkt("POINT (1120351.57 741921.42)")
    #     point.Transform(transform)
    #
    #     outlet_xg = point.ExportToWkt()[0]
    #     outlet_y = point.ExportToWkt()[1]

    # # To TEST only
    # source = osr.SpatialReference()
    # source.ImportFromEPSG(2927)
    #
    # target = osr.SpatialReference()
    # target.ImportFromEPSG(4326)
    #
    # transform = osr.CoordinateTransformation(source, target)
    #
    # point = ogr.CreateGeometryFromWkt("POINT (1120351.57 741921.42)")
    # point.Transform(transform)
    #
    # outlet_x = point # TODO: get the x and Y from this string point


    # # ----------- projection --------------------

    return outlet_x, outlet_y

def get_box_xyxy_from_shp_shx(shp_file, shx_file, simulation_folder='/usr/lib/tethys/src/tethys_apps/tethysapp/my_first_app/workspaces/user_workspaces/usr1/'):
    from shapely.geometry import shape

    # convert the django_memory_file format to original shapefile
    filename = "watershed.shp"  # received file name
    file_obj = shp_file
    with open(simulation_folder +'/' + filename, 'w') as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)
    shp_file = simulation_folder +'/' + filename

    # convert the django_memory_file format to original shapefile
    filename = "watershed.shx"  # received file name
    file_obj = shx_file
    with open(simulation_folder +'/' + filename, 'w') as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)
    shx_file = simulation_folder +'/' + filename


    c = fiona.open(shp_file)

    # first record
    first_shape = c.next()

    # shape(first_shape['geometry']) -> shapely geometry

    box_topY = shape(first_shape['geometry']).bounds[3]
    box_bottomY = shape(first_shape['geometry']).bounds[1]
    box_rightX = shape(first_shape['geometry']).bounds[2]
    box_leftX = shape(first_shape['geometry']).bounds[0]

    return box_rightX, box_bottomY, box_leftX, box_topY

def run_model_with_input_as_dictionary(inputs_dictionary,write_to_db=True, simulation_folder=""):
    """
    :param inputs_dictionary:   inputs converted to dictionary in validation step. Type of inouts are taken care of
                                e.g. float is already a float type, int is int, and string is string.
    :param simulation_folder:
    :return:                    Hydrograph (as timeseries, between datetime Vs Discharge)
    """
    # inputs extracted from the dictionary

    user_name = inputs_dictionary['user_name']
    simulation_name = inputs_dictionary['simulation_name']
    simulation_folder = simulation_folder
    simulation_start_date = inputs_dictionary['simulation_start_date']
    simulation_end_date = inputs_dictionary['simulation_end_date']
    USGS_gage = int(inputs_dictionary['USGS_gage'])

    outlet_x = float(inputs_dictionary['outlet_x'])
    outlet_y = float(inputs_dictionary['outlet_y'])
    box_topY = float(inputs_dictionary['box_topY'])
    box_bottomY = float(inputs_dictionary['box_bottomY'])
    box_rightX = float(inputs_dictionary['box_rightX'])
    box_leftX = float(inputs_dictionary['box_leftX'])

    timeseries_source = inputs_dictionary['timeseries_source']
    threshold = float(inputs_dictionary['box_bottomY'])
    cell_size = float(inputs_dictionary['box_bottomY'])
    timestep = float(inputs_dictionary['box_bottomY'])
    model_engine = inputs_dictionary['model_engine']

    # :todo some sort of algorith to create a folder name. ini_fname = simulation_name OR may not be required
    temp_folder_name = 'usr1'
    ini_fname = 'BlackSmithFork.ini'

    simulation_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'workspaces', 'user_workspaces',
                                     temp_folder_name)
    ini_path = os.path.join(simulation_folder, ini_fname)

    # TOPKAPI MODEL
    if model_engine == 'TOPKAPI':
        # step0,
        run_1 = pytopkapi_run_instance(simulation_name=simulation_name, cell_size=cell_size, timestep=timestep,
                                       xy_outlet=[outlet_x, outlet_y],
                                       yyxx_boundingBox=[box_topY, box_bottomY, box_leftX, box_rightX],
                                       USGS_gage=USGS_gage, list_of_threshold=[threshold],
                                       simulation_folder=simulation_folder)

        step1_create_ini = run_1.prepare_supporting_ini()  # step1
        # step2_run_model = run_1.run()                               # step2
        date_in_datetime, Qsim, error = run_1.get_Qsim_and_error()

        if write_to_db:
            # write_to_db_input_as_dictionary(inputs_dictionary, simulation_folder)
            table_id = write_to_db_input_as_dictionary(inputs_dictionary, simulation_folder)

        # create_viewplot_hydrograph(date_in_datetime, Qsim, error)  # aile kina ho kaam garena

        # preparing timeseries data in the format shown in: http://docs.tethysplatform.org/en/latest/tethys_sdk/gizmos/plot_view.html#time-series
        hydrograph_series = []
        date_broken = [[dt.year, dt.month, dt.day, dt.hour, dt.minute] for dt in date_in_datetime]
        for i in range(len(Qsim)):
            date = datetime(year=date_broken[i][0], month=date_broken[i][1], day=date_broken[i][2],
                            hour=date_broken[i][3],
                            minute=date_broken[i][4])
            hydrograph_series.append([date, float(Qsim[i])])

    return hydrograph_series, table_id

def validate_inputs(request):
    """

    :param                  : HTTP request
    :return:
        Validation status   :True if valid form, False if something wrong with the form
        Form Error          :If there is something wrong, gives a superficial error message
        inputs_dictionary   :If form is complete, returns the list of inputs as a dictionary
    """

    # defaults
    error_msg = ""
    inputs = {}
    inputs_dictionary = {}

    # All these inputs should go in the validation functions itself, not here in the front


    outlet_y = float(request.POST['outlet_y'])
    outlet_x = float(request.POST['outlet_x'])
    box_topY = float(request.POST['box_topY'])
    box_bottomY = float(request.POST['box_bottomY'])
    box_rightX = float(request.POST['box_rightX'])
    box_leftX = float(request.POST['box_leftX'])



    # # If UEB, TOPNET or RHESSys, print "Not ready yet"
    # if request.POST['timeseries_source'] != "UEB":
    #     error_msg = "Time series you selected is not ready yet"

    if request.POST['model_engine'] != "TOPKAPI":
        error_msg = "Error 1: "+"Model you selected is not ready yet"
        validation_status = False

    # # Check Validity of USGS gage

    # # From RADIO BOX (not created so far), make sure inputs is read here so no IF required

    # # Ask confirmation of shapefile inputs
    shapefile_radio = False
    if shapefile_radio:
        # get the outlet x,y and the bounding box
        try:
            # because shp files are more than one, we interate
            for afile in request.FILES.getlist('outlet_shp'):

                if afile.name.split(".")[-1] == "shp":
                    outlet_shp = afile
                if afile.name.split(".")[-1] == "shx":
                    outlet_shx = afile
                if afile.name.split(".")[-1] == "prj":
                    outlet_prj = afile
                if afile.name.split(".")[-1] == "dbf":
                    outlet_dbf = afile

            outlet_x, outlet_y = get_outlet_xy_from_shp_shx(shp_file=outlet_shp, shx_file=outlet_shx)


        except Exception, e:
            error_msg = "Error 2: "+ str(e)
            validation_status = False

        try:
            for afile in request.FILES.getlist('watershed_shp'):

                if afile.name.split(".")[-1] == "shp":
                    watershed_shp = afile
                if afile.name.split(".")[-1] == "shx":
                    watershed_shx = afile
                if afile.name.split(".")[-1] == "prj":
                    watershed_prj = afile
                if afile.name.split(".")[-1] == "dbf":
                    watershed_dbf = afile

            box_rightX, box_bottomY, box_leftX, box_topY = get_box_xyxy_from_shp_shx(shp_file=watershed_shp,shx_file=watershed_shx)


        except Exception, e:
            error_msg = "Error 3: "+ str(e)
            validation_status = False

    # domain validation, make sure this contains US
    if not -90.0 < outlet_y < 90.0:
        error_msg = "Error 4: "+'Outlet shapefile should be in WGS 84 coordinate system'
        validation_status = False
    if not -180.0 < outlet_x < 180.0:
        error_msg = "Error 4: "+'Outlet shapefile should be in WGS 84 coordinate system'
        validation_status = False

    if not -90.0 < box_bottomY < 90.0:
        error_msg = "Error 5: "+'Watershed shapefile should be in WGS 84 coordinate system'
        validation_status = False

    if not -180.0 < box_rightX < 180.0:
        error_msg = "Error 5: "+'Watershed shapefile should be in WGS 84 coordinate system'
        validation_status = False


    if error_msg == "" or error_msg.startswith("Error 2") or error_msg.startswith("Error 3"):
        validation_status = True

        # create a dictinary of inputs. This helps carry program forward, eliminating the need to parse inputs again
        inputs_dictionary = {  "user_name":  request.user.username,
                    "simulation_name": request.POST['simulation_name'],
                    "simulation_start_date" : request.POST['simulation_start_date_picker'],
                    "simulation_end_date" : request.POST['simulation_end_date_picker'],
                    "USGS_gage" : int(request.POST['USGS_gage']),

                    "outlet_y": float(outlet_y),
                    "outlet_x": float(outlet_x),
                    "box_topY" : float(box_topY),
                    "box_bottomY" : float(box_bottomY),
                    "box_rightX": float(box_rightX),
                    "box_leftX" : float(box_leftX),

                    "timeseries_source": request.POST['timeseries_source'],

                    "threshold": int(request.POST['threshold']),
                    "cell_size": float(request.POST['cell_size']),
                    "timestep": float(request.POST['timestep']),
                    "model_engine":request.POST['model_engine'],

            }

    else:
        validation_status = False

    return validation_status, error_msg, inputs_dictionary

def write_to_db_input_as_dictionary(inputs_dictionary, simulation_folder=""):
    """
     :param inputs_dictionary:
    :param simulation_folder:
    :return: table_id of (pk) of the run information added to the dictionary
    """

    user_name = inputs_dictionary['user_name']
    simulation_name = inputs_dictionary['simulation_name']
    simulation_start_date = inputs_dictionary['simulation_start_date']
    simulation_end_date = inputs_dictionary['simulation_end_date']
    USGS_gage = int(inputs_dictionary['USGS_gage'])

    outlet_x = float(inputs_dictionary['outlet_x'])
    outlet_y = float(inputs_dictionary['outlet_y'])
    box_topY = float(inputs_dictionary['box_topY'])
    box_bottomY = float(inputs_dictionary['box_bottomY'])
    box_rightX = float(inputs_dictionary['box_rightX'])
    box_leftX = float(inputs_dictionary['box_leftX'])

    timeseries_source = inputs_dictionary['timeseries_source']
    threshold = float(inputs_dictionary['threshold'])
    cell_size = float(inputs_dictionary['cell_size'])
    timestep = float(inputs_dictionary['timestep'])

    model_engine = inputs_dictionary['model_engine']

    # other model parameter is string or text, combining parametes with __ (double underscore)
    other_model_parameters = str(timeseries_source)+ "__"+ str(threshold) + "__"+ str(cell_size) + "__"+ str(timestep)

    # :TODO write only when sim_name is different for a user
    from .model import engine,Base, SessionMaker, model_inputs_table, model_calibration_table
    # model_calibration_table.__table__.drop(engine)   # to delete the tables, in case anything wrong goes
    # model_inputs_table.__table__.drop(engine)
    # Base.metadata.create_all(engine)    # Create tables
    session = SessionMaker()            # Make session

    # one etnry / row
    one_run = model_inputs_table(user_name=user_name, simulation_name=simulation_name,simulation_folder=simulation_folder,
            simulation_start_date=simulation_start_date,simulation_end_date=simulation_end_date,USGS_gage=USGS_gage,
                 outlet_x=outlet_x,outlet_y=outlet_y, box_topY=box_topY,box_bottomY=box_bottomY, box_rightX=box_rightX,box_leftX=box_leftX,
                 model_engine=model_engine, other_model_parameters=other_model_parameters )
    session.add(one_run)
    session.commit()

    # read the id
    current_model_inputs_table_id = str(len(session.query(model_inputs_table).filter(
        model_inputs_table.user_name == user_name).all()))  # because PK is the same as no of rows, i.e. length

    return current_model_inputs_table_id
# # UN-USED or INCOMPLETE functions
def call_subprocess(cmdString, debugString):
    cmdargs = shlex.split(cmdString)
    debFile = open('debug_file.txt', 'w')
    debFile.write('Starting %s \n' % debugString)
    retValue = subprocess.call(cmdargs,stdout=debFile)
    if (retValue==0):
        debFile.write('%s Successful\n' % debugString)
        debFile.close()
    else:
        debFile.write('There was error in %s\n' % debugString)
        debFile.close()
def change_point_to_WGS84(list_of_points, in_shp_file):

    """
    :param list_of_points: a python list of points to be transformed to WGS 1984
    :param in_shp_file: shapefile, to read its input projection
    :return: a list of transformed points

    Helper Source:
    http://zevross.com/blog/2014/06/09/no-esri-no-problem-manipulate-shapefiles-with-the-python-library-osgeo/
    http://geoinformaticstutorial.blogspot.com/2012/10/reprojecting-shapefile-with-gdalogr-and.html
    """

    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataSource = driver.Open(in_shp_file, 0)  # 0 means read-only, 1 means writeable
    layer = dataSource.GetLayer()

    sourceprj = layer.GetSpatialRef()
    targetprj = osr.SpatialReference()
    targetprj.ImportFromEPSG(4326)
    transform = osr.CoordinateTransformation(sourceprj, targetprj)

    #
    # # convert the points to WGS 84
    # point = ogr.CreateGeometryFromWkt("POINT (%s %s)"%(outlet_x,outlet_y ) )
    # point.Transform(transform)
    #
    # outlet_x = point.ExportToWkt()[0]
    # outlet_y = point.ExportToWkt()[1]
    #
    # #
    # # return list_of_transferred_points
def handle_uploaded_file(f):
    with open('some/file/name.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
def load_shapefile_to_db(shapefile_base="/usr/lib/tethys/src/tethys_apps/tethysapp/my_first_app/workspaces/user_workspaces/usr1/outlet_boundary/Wshed_BlackSmithFork", db='Spatial_dataset_service1'):
    # https://github.com/tethysplatform/tethys/blob/master/docs/tethys_sdk/spatial_dataset_services.rst

    from tethys_sdk.services import get_spatial_dataset_engine

    # create connection to "spatial data service" engine
    dataset_engine = get_spatial_dataset_engine(name=db)

    # # TODO: check if this is deleted later
    # # Example method with debug option
    # dataset_engine.list_layers(debug=True)

    # Create a workspace named after our app
    dataset_engine.create_workspace(workspace_id='my_first_app', uri='my-first-app')

    # Path to shapefile base for foo.shp, side cars files (e.g.: .shx, .dbf) will be
    # gathered in addition to the .shp file.
    shapefile_base = shapefile_base

    # Notice the workspace in the store_id parameter
    result = dataset_engine.create_shapefile_resource(store_id='my_first_app:Wshed_BlackSmithFork', shapefile_base=shapefile_base)

    # Check if it was successful
    if not result['success']:
        return result['error']
        raise



    return result['result']
def write_input_parameters_to_db(user_name, simulation_name, input_parameters_string, calibration_parameter_string):
    # NOT USED

    # write the inputs to the database
    from .model import engine, SessionMaker, Base, model_inputs_table, model_calibration_table

    Base.metadata.create_all(engine)  # Create tables
    session = SessionMaker()  # Make session

    one_run = model_inputs_table(user_name, input_parameters_string, calibration_parameter_string)

    session.add(one_run)
    session.commit()

    # read the id
    current_model_inputs_table_id = str(len(session.query(model_inputs_table).filter(
        model_inputs_table.user_name == user_name).all()))  # because PK is the same as no of rows, i.e. length

    return current_model_inputs_table_id

# # In test phase functions
def test_hds():

    path = os.path.dirname(os.path.realpath(__file__)) + "/hydrogate_python_client"
    sys.path.append(path)

    from hydrogate import HydroDS

    # Create HydroDS object passing user login account for HydroDS api server
    HDS = HydroDS(username='pdahal', password="pDahal2016")

    workingDir = '/home/prasanna/Documents/test'
    #
    # # Set parameters for watershed delineation
    # streamThreshold = 100;  pk_min_threshold = 1000;  pk_max_threshold = 10000;  pk_num_thershold = 12
    #
    # # model start and end dates
    # startDateTime = "2010/10/01 0"; endDateTime = "2011/06/01 0"
    # start_year = 2000; end_year = 2010


    # #upload DEM 30 m for C22 Watershed
    DEM_30M = workingDir + '/DEM_Prj_f.tif'
    upload_30m_DEM =HDS.upload_file(file_to_upload=DEM_30M)     # file is projected
    print "DEM raster uploaded. The location of the DEM is: ", upload_30m_DEM

    # upload shapefiles
    outlet = workingDir + '/Outlet_BlackSmithFork.zip'
    wshed = workingDir + '/Outlet_BlackSmithFork.zip'
    upload_outlet = HDS.upload_file(file_to_upload=outlet)   # file is projected
    upload_wshed = HDS.upload_file(file_to_upload=wshed)        # file is projected
    print "Shapefiles uploaded. The location of the outlet is: ", upload_outlet

    hs_obj = HydroshareResource(upload_30m_DEM)
    hs_obj.add(upload_outlet)
    hs_obj.add(upload_wshed)
class HydroshareResource(object):
    from hs_restclient import HydroShare, HydroShareAuthBasic
    def __init__(self, fpath="", username = "prasanna_310",  password = "Hydrology12!@" ):
        self.username = "prasanna_310"
        self.password = "Hydrology12!@"
        
        from hs_restclient import HydroShare, HydroShareAuthBasic
        auth = HydroShareAuthBasic(username=username, password=password)
        self.hs = HydroShare(auth=auth)

        self.day = date.today().strftime('%m/%d/%Y')
        self.abstract = 'The files created from hydrologic modeling app'
        self.title = 'Model input files'
        self.keywords = ('hydrologic modeling', 'app', 'tethys', 'TOPKAPI', 'RHEHSSys')
        self.rtype = 'GenericResource'
        self.metadata = '[{"coverage":{"type":"period", "value":{"start":"%s", "end":"%s"}}}, {"creator":{"name":"%s"}}]'%(self.day,self.day,self.username)
        self.fpath = fpath

        self.first_resource_id = self.hs.createResource(self.rtype, self.title, resource_file=self.fpath, keywords=self.keywords, abstract=self.abstract,
                                        metadata=self.metadata)
        print "Resource created Resource ID is: ", self.first_resource_id


    def add(self,fpath):
        resource_id = self.hs.addResourceFile(self.first_resource_id, fpath)
        print "Resource added Resource ID is: ", self.first_resource_id
        return resource_id


if __name__ == "__main__":
    working_dir = '/home/prasanna/tethysdev/tethysapp-my_first_app/tethysapp/my_first_app/workspaces/user_workspaces/usr1/retreived'
    outlet_shp = '/home/prasanna/tethysdev/tethysapp-my_first_app/tethysapp/my_first_app/workspaces/user_workspaces/usr1/outlet_boundary/Outlet_BlackSmithFork.shp'
    wshed_shp = '/home/prasanna/tethysdev/tethysapp-my_first_app/tethysapp/my_first_app/workspaces/user_workspaces/usr1/outlet_boundary/Wshed_BlackSmithFork.shp'

    # print "Creating and Adding to hydroshare....."
    # hs_object = HydroshareResource(wshed_shp)
    # resID2 = hs_object.add(outlet_shp)
    #
    # print "Retreiving data from hydroshare......."
    # auth = HydroShareAuthBasic(username='prasanna_310', password='Hydrology12!@')
    # hs = HydroShare(auth=auth)
    # file_to_retreive = 'Wshed_BlackSmithFork.shp'
    # hs.getResourceFile(resID2, 'Wshed_BlackSmithFork.shp', destination=working_dir)

    test_hds()


