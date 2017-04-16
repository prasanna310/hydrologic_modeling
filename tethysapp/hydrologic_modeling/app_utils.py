from datetime import datetime
import subprocess, shlex

import os, sys

try:
    import fiona
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




# import sys
# sys.path.append('/utils')
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
                         "simulation_folder":'',


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

    # modify the input_dictionary based on file (shapefile, geojson) inputs,

    # if the input is hydroshare id
    if request.POST['outlet_hs']:
        pass
    if request.POST['bounding_box_hs']:
        pass

    return inputs_dictionary


def read_hydrograph_from_txt(hydrograph_series_fname=None):


    if hydrograph_series_fname == None:
        hydrograph_series_fname = '/home/prasanna/tethysdev/hydrologic_modeling/tethysapp/hydrologic_modeling/workspaces/user_workspaces/usr1/abebebsb323bsg1283bg3.txt'
    hs_resource_id_created = os.path.basename(hydrograph_series_fname).split(".")[0]  # assuming the filename is the hydroshare resource ID

    # df = pd.read_csv(f, names=['year' , 'month' , 'day', 'hour', 'minute', 'q_obs', 'q_sim'])  # parse_dates=[0], infer_datetime_format=True
    # # df2 = pd.read_csv(f, names=['date','q_obs', 'q_sim'], parse_dates=[0], infer_datetime_format=True)
    # d = np.array(df['DateTime'])
    # q_obs = np.array(df['q_obs'])
    # q_sim = np.array(df['q_sim'])
    # ar = zip(d, float(q_obs), float(q_sim))

    ar = np.genfromtxt(hydrograph_series_fname, delimiter="\t")
    hydrograph = []
    for i in range(len(ar)):
        date = datetime(year= int(ar[i][0]), month=int(ar[i][1]), day=int(ar[i][2]), hour=int(ar[i][3]),   minute=int(ar[i][4]))
        hydrograph.append([date, float(ar[i][5]),  float(ar[i][6])])

    return hydrograph, hs_resource_id_created


def create_model_input_dict_from_db( user_name=None , hs_resource_id=None, model_input_id=None ):
    """
    A function that creates input dictionary by querin the db. Accepts either hs_resource_id, or model_input_id to create
    the input dicitonary.
    :param model_inputs_table_id:  primary key id for the model_input table
    :param hs_resource_id:         Hydroshare resource id for the model_input table
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
    print 'MSG: model_input ID for which rest of the inputs are being retrieved: ', hs_resource_id

    if hs_resource_id != None:
        all_rows = session.query(model_inputs_table). \
            filter(and_(model_inputs_table.hs_resource_id == hs_resource_id,
                        model_inputs_table.user_name == user_name)).all()

    if model_input_id != None:
        all_rows = session.query(model_inputs_table).\
            filter(and_(model_inputs_table.id== model_input_id, model_inputs_table.user_name == user_name)).all()

    # :TODO for a particular user_name also requird. Can be poorly achieved by writing if-clause in for-loop below


    # retrieve the parameters and write to a dictionary
    inputs_dictionary = {}

    for row in all_rows:
        inputs_dictionary['id'] = row.id
        inputs_dictionary['user_name'] = row.user_name
        inputs_dictionary['simulation_name'] = row.simulation_name
        inputs_dictionary['simulation_folder'] = row.hs_resource_id
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

        inputs_dictionary['remarks'] = row.remarks
        inputs_dictionary['user_option'] = row.user_option
        inputs_dictionary['model_engine'] = row.model_engine


    print 'MSG: SUCCESS Querrying the database to create dictionary '
    if inputs_dictionary == {}:
        print "MSG: ERROR, HydroShare resource ID invalid!!! "

    return  inputs_dictionary

def create_simulation_list_after_querying_db(given_user_name=None, return_hs_resource_id=True, return_model_input_id = False):
    # returns a tethys gizmo or a drop down list, which should be referenced in html with name = 'simulation_names_list'
    # if return_hs_resource_id == True,
    from .model import engine, SessionMaker, Base, model_inputs_table ,model_calibration_table, model_result_table
    from tethys_sdk.gizmos import SelectInput

    Base.metadata.create_all(engine)    # Create tables
    session = SessionMaker()            # Make session

     # Query DB
    simulations_queried = session.query(model_inputs_table).filter(model_inputs_table.user_name==given_user_name).all() # searches just the id input in URL

    # print 'Total no of records in model input table is', session.query(model_inputs_table).count()
    # print 'Total no of records in model calibration table is', session.query(model_calibration_table).count()
    # print 'Total no of records in model result table is', session.query(model_result_table).count()

    simulation_names_list_queried = []
    simulation_names_id = []
    hs_resourceID = []
    queries = []

    for record in simulations_queried:
        simulation_names_list_queried.append(record.simulation_name)
        simulation_names_id.append(record.id)
        hs_resourceID.append(record.hs_resource_id)


    if return_model_input_id :
        queries = zip(simulation_names_list_queried,simulation_names_id ) # returns model_input_table_id
    if return_hs_resource_id :
        queries = zip(simulation_names_list_queried, hs_resourceID)  # returns hs_resource of model instance


    simulation_names_list = SelectInput(display_text='Saved Models',
                                     name='simulation_names_list',
                                     multiple=False,
                                     options= queries  )#[ (  simulations_queried[0].id, '1'),  (  simulations_queried[1].simulation_name, '2'  ),  (   simulations_queried[1].user_name, '2'  )]

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
            # write_to_model_input_table(inputs_dictionary, simulation_folder)
            table_id = write_to_model_input_table(inputs_dictionary, simulation_folder)

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

def shapefile_to_geojson(path_to_shp):
    #input: Shapefile
    #output: geojson that the javascript can plot

    # shapefile to geojson using gdal
    directory, filename = os.path.split(path_to_shp)
    path_to_geojson = os.path.join(directory, "watershed.geojson")
    cmd = '''ogr2ogr -f GeoJSON -t_srs crs:84 %s %s'''%(path_to_geojson, path_to_shp)
    print cmd
    os.system(cmd)


    # edit geojson
    def json_to_js_prepend(json_filename):
        import fileinput

        # STEP1: add ) at the last line
        geojson_file = file(json_filename, 'a')
        geojson_file.write(')')
        geojson_file.close()

        # STEP2: add in the beginning based on http://stackoverflow.com/questions/5914627/prepend-line-to-beginning-of-a-file
        f = fileinput.input(json_filename, inplace=1)
        line_to_prepend = 'geojson_callback('
        for xline in f:
            if f.isfirstline():
                print line_to_prepend.rstrip('\r\n') + '\n' + xline,
            else:
                print xline,

    json_to_js_prepend(path_to_geojson)
    return path_to_geojson





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
    geojson_files = {} #:TODO if geosjson, its input should supercede other inputs. So may be write code at last

    # All these inputs should go in the validation functions itself, not here in the front


    outlet_y = float(request.POST['outlet_y'])
    outlet_x = float(request.POST['outlet_x'])
    box_topY = float(request.POST['box_topY'])
    box_bottomY = float(request.POST['box_bottomY'])
    box_rightX = float(request.POST['box_rightX'])
    box_leftX = float(request.POST['box_leftX'])



    # # If UEB, TOPNET or RHESSys, print "Not ready yet"
    # if request.POST['timeseries_source'] != "Daymet":
    #     error_msg = "Time series you selected is not ready yet"

    if request.POST['model_engine'] != "TOPKAPI":
        error_msg = "Error 1: "+"Model you selected is not ready yet"
        validation_status = False

    # # Check Validity of USGS gage

    # # From RADIO BOX (not created so far), make sure inputs is read here so no IF required

    # # Ask confirmation of shapefile inputs
    shapefile_radio = True
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
            geojson_files['geojson_outlet']  = shapefile_to_geojson(outlet_shp)



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

            # lines below are not being executed
            # box_rightX, box_bottomY, box_leftX, box_topY = get_box_xyxy_from_shp_shx(shp_file=watershed_shp,shx_file=watershed_shx)
            geojson_files['geojson_domain'] = shapefile_to_geojson(watershed_shp)


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

    return validation_status, error_msg, inputs_dictionary, geojson_files

def generate_uuid_file_path(file_name=None, root_path= None):
    if root_path == None:
        root_path = os.path.join(os.path.dirname(__file__),'workspaces', 'user_workspaces')
    from uuid import uuid4
    uuid_path = os.path.join(root_path, uuid4().hex)
    os.makedirs(uuid_path)
    file_path = uuid_path
    if file_name:
        file_path = os.path.join(uuid_path, file_name)
    return file_path


def write_to_model_input_table(inputs_dictionary, hs_resource_id=""):
    """
     :param inputs_dictionary:
    :param hs_resource_id_created:
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
    
    # :TODO, take these values from from input_dictionary
    remarks = ''
    user_option = ''

    # other model parameter is string or text, combining parametes with __ (double underscore)
    other_model_parameters = str(timeseries_source)+ "__"+ str(threshold) + "__"+ str(cell_size) + "__"+ str(timestep)

    # :TODO write only when sim_name is different for a user
    from .model import engine,Base, SessionMaker, model_inputs_table, model_calibration_table
    # model_calibration_table.__table__.drop(engine)   # to delete the tables, in case anything wrong goes
    # model_inputs_table.__table__.drop(engine)
    # Base.metadata.create_all(engine)    # Create tables
    session = SessionMaker()            # Make session

    # one etnry / row
    one_run = model_inputs_table(user_name=user_name, simulation_name=simulation_name,hs_resource_id=hs_resource_id,
            simulation_start_date=simulation_start_date,simulation_end_date=simulation_end_date,USGS_gage=USGS_gage,
                 outlet_x=outlet_x,outlet_y=outlet_y, box_topY=box_topY,box_bottomY=box_bottomY, box_rightX=box_rightX,box_leftX=box_leftX,
                 model_engine=model_engine, other_model_parameters=other_model_parameters, remarks=remarks, user_option=user_option )
    session.add(one_run)
    session.commit()
    print "Run details written successfully to model_input_table"

    # read the id
    current_model_inputs_table_id = str(len(session.query(model_inputs_table).filter(
        model_inputs_table.user_name == user_name).all()))  # because PK is the same as no of rows, i.e. length

    return current_model_inputs_table_id

def write_to_model_calibration_table(model_input_table_id, numeric_parameters_list=None, calibration_parameters_list=None):
    '''
    list, which will be converted string separated by __ double underscore
    :param numeric_parameters_list:   [pvs_t0, vo_t0 , qc_t0, kc] for topkapi
    :param calib_parameters_list:     [fac_l, fac_ks, fac_n_o, fac_n_c, fac_th_s]
    :param model_input_table_id:      The foreign key
    :return:
    '''
    if numeric_parameters_list == None:
        numeric_parameters_list = [90.0,100.0,0,1]
    if calibration_parameters_list == None:
        calibration_parameters_list = [1,1,1,1,1]

    # make the exam same list, but change numbers to string
    numeric_parameters_list = [str(item) for item in numeric_parameters_list]
    calibration_parameters_list = [str(item) for item in calibration_parameters_list]

    # Database accepts string, so combining parametes with __ (double underscore)
    numeric_parameters = '__'.join(numeric_parameters_list)
    calibration_parameters = '__'.join(calibration_parameters_list)

    # :TODO write only when sim_name is different for a user
    from .model import engine, Base, SessionMaker,  model_calibration_table
    session = SessionMaker()  # Make session

    # one etnry / row
    one_run = model_calibration_table(numeric_parameters= numeric_parameters,
                                      calibration_parameters=calibration_parameters,input_table_id=model_input_table_id)
    session.add(one_run)
    session.commit()
    print "Run details written successfully to model_calibration_table"

    # read the id
    # current_model_calibration_table_id = str(len(session.query(model_calibration_table).filter(
    #     model_calibration_table.input_table_id == model_input_table_id).all()))  # because PK is the same as no of rows, i.e. length

    all_row = session.query(model_calibration_table).filter(model_calibration_table.input_table_id == model_input_table_id).all()
    current_model_calibration_table_id  = all_row[0].id # this query will only give one row. For that row, give id


    return current_model_calibration_table_id

def write_to_model_result_table(model_calibration_table_id, timeseries_discharge_list):
    '''
    :param: model_calibration_table_id:     The foriegn ID to reference the model_calibration_table
    :param timeseries_discharge_list:       [   [datetime.datetime(2015, 1, 1, 0, 0), 2.0, 3.1],  [datetime.datetime(2015, 1, 2, 0, 0),2.35, 3.5]   ]
    :return:
    '''
    from .model import  SessionMaker,  model_result_table
    session = SessionMaker()

    # one_timestep =  [datetime.datetime(2015, 1, 1, 0, 0), 2.0, 3.1]       # example
    for one_timestep in timeseries_discharge_list:
        # one etnry / row
        one_run = model_result_table(date_time=one_timestep[0], simulated_discharge=one_timestep[1],
                                     observed_discharge=one_timestep[2], model_calibration_id =model_calibration_table_id)
        session.add(one_run)
    session.commit()
    print "Run details written successfully to model_results_table"
    return





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
    #from hs_restclient import HydroShare, HydroShareAuthBasic
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


