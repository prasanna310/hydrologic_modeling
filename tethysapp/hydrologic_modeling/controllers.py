from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .model import SessionMaker
from tethys_gizmos.gizmo_options import TextInput, DatePicker
from tethys_sdk.gizmos import SelectInput
from tethys_sdk.gizmos import TimeSeries, AreaRange, PlotView, LinePlot
from tethys_apps.sdk.gizmos import *
import datetime

import sys, os, json
sys.path.append('/utils')

sys.path.append(os.path.abspath('/utils/pytopkapi_utils.py'))
sys.path.append(os.path.abspath(os.path.abspath(os.path.dirname(__file__) )))

from utils.pytopkapi_utils import *
import app_utils

# try:
#     from .app_utils import *
# except Exception,e:
#     print e

# :TODO -> make sure db is written after model is ran

# instead of writing arbitrary error, it might be a good idea to use this dictionary in returning errors
# this dictionary should be in a different file
errors = {'invalid_date':'Error 1001. Input type invalid',
          'invalid_outlet':'Error xx. Timeseries source selected not yet ready',
          'invalid_domain':'Error xx. Domain source selected not yet ready',
          'invalid_USGS_gage': 'Error xx. USGS gage selected not correct, or not data not available for it',
          }

@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    context = {}

    return render(request, 'hydrologic_modeling/home.html', context)




def model_input(request):

    user_name = request.user.username

    # Define Gizmo Options
    # from .model import engine, SessionMaker, Base, model_inputs_table, model_calibration_table

    # Query DB for gage objects, all the entries by the user name
    # give the value for thsi variable = 0 if the program is starting for the first time
    simulation_names_list = app_utils.create_simulation_list_after_querying_db(given_user_name=user_name)


    simulation_name = TextInput(display_text='Simulation name', name='simulation_name', initial='Logan_sample')
    USGS_gage = TextInput(display_text='USGS gage nearby', name='USGS_gage', initial='10109000')
    cell_size = TextInput(display_text='Cell size in meters', name='cell_size', initial='300')
    timestep = TextInput(display_text='Timestep in hrs', name='timestep', initial='24') #, append="hours"
    simulation_start_date_picker = DatePicker(name='simulation_start_date_picker', display_text='Start Date',
                                              autoclose=True, format='mm-dd-yyyy', start_date='10-15-2005',
                                              start_view='year', today_button=True, initial='01-01-2010')
    simulation_end_date_picker = DatePicker(name='simulation_end_date_picker', display_text='End Date',
                                            autoclose=True, format='mm-dd-yyyy', start_date='10-15-2005',
                                            start_view='year', today_button=False, initial='12-30-2011')

    timeseries_source = SelectInput(display_text='Timeseries source',
                name='timeseries_source',
                multiple=False,
                options=[('User File', 'user_file'), ('UEB', 'UEB'), ('Daymet', 'Daymet')],
                initial=['Daymet'],
                original=['Daymet'])

    model_engine = SelectInput(display_text='Choose Model',
                name='model_engine',
                multiple=False,
                options=[('TOPKAPI', 'TOPKAPI'), ('TOPNET', 'TOPNET'), ('RHESSys', 'RHESSys')],
                initial=['TOPKAPI'],
                original=['TOPKAPI'])

    threshold = TextInput(display_text='Stream threshold in km2', name='threshold', initial='25')

    # html form to django form (for LOGAN WATERSHED)
    outlet_x = TextInput(display_text='Longitude', name='outlet_x', initial='-111.7836')
    outlet_y = TextInput(display_text='Latitude', name='outlet_y', initial='41.744')

    box_topY = TextInput(display_text='North Y', name='box_topY', initial='42.128')
    box_rightX = TextInput(display_text='East X', name='box_rightX', initial='-111.438')
    box_leftX = TextInput(display_text='West X', name='box_leftX', initial='-111.822')
    box_bottomY = TextInput(display_text='South Y', name='box_bottomY', initial='41.686')

    # (NEW FOR LOGAN WATERSHED)
    # outlet_x = TextInput(display_text='Longitude', name='outlet_x', initial='-111.7915') #41.74025, -111.7915
    # outlet_y = TextInput(display_text='Latitude', name='outlet_y', initial='41.74025')

    box_topY = TextInput(display_text='North Y', name='box_topY', initial='41.90')
    box_rightX = TextInput(display_text='East X', name='box_rightX', initial='-111.54')
    box_leftX = TextInput(display_text='West X', name='box_leftX', initial='-111.85')
    box_bottomY = TextInput(display_text='South Y', name='box_bottomY', initial='41.72')


    # FOR PLUNGE
    outlet_x = TextInput(display_text='Longitude', name='outlet_x', initial='-117.141284')
    outlet_y = TextInput(display_text='Latitude', name='outlet_y', initial='34.12128')

    box_topY = TextInput(display_text='North Y', name='box_topY', initial='34.2336')
    box_rightX = TextInput(display_text='East X', name='box_rightX', initial='-117.048046')
    box_leftX = TextInput(display_text='West X', name='box_leftX', initial='-117.168289')
    box_bottomY = TextInput(display_text='South Y', name='box_bottomY', initial='34.10883')


    outlet_hs = TextInput(display_text='', name='outlet_hs', initial='')
    bounding_box_hs = TextInput(display_text='', name='bounding_box_hs', initial='')

    existing_sim_res_id = TextInput(display_text='', name='existing_sim_res_id', initial='')

    form_error = ""
    observed_hydrograph = ""
    test_function_response = ""
    geojson_files = {}
    geojson_outlet = 'Default'
    geojson_domain = 'Default'
    table_id = 0
    validation_status = True

    # when it receives request. This is not in effect. Currently, the request is sent to model_run, not model_input.html
    if request.is_ajax and request.method == 'POST':
        try:
            validation_status, form_error, inputs_dictionary, geojson_files = app_utils.validate_inputs(request) # input_dictionary has proper data type. Not everything string
            # if geojson_files != {}:
            #     for geojson in geojson_files.keys():
            #         if geojson == 'geojson_outlet':
            #             geojson_outlet = geojson_files['geojson_outlet']
            #         if geojson == 'geojson_domain':
            #             geojson_domain = geojson_files['geojson_domain']


            if form_error.startswith("Error 2") or form_error.startswith("Error 3"):  # may not need this part. Because if no shapefile input, will not read it
                form_error = ""

        except Exception, e:
            if form_error.startswith("Error 2") or form_error.startswith("Error 3"):  # may not need this part. Because if no shapefile input, will not read it
                form_error = ""
            else:
                form_error = "Error 0: " + str(e)

        if not validation_status:
            # useless code. If the file is prepared, we know validatoin status = False
            import numpy as np
            np.savetxt("/home/prasanna/Documents/a%s.txt"%form_error, np.array([1, 1]))

        if validation_status:
            # hydrograpph series is a series (list) object.
            # table_id is the id of the data just written in the database after the successful model run
            hydrograph_series = []
            # hydrograph_series, table_id = app_utils.run_model_with_input_as_dictionary(inputs_dictionary,False, simulation_folder="")


            observed_hydrograph = TimeSeries(
                height='500px',
                width='500px',
                engine='highcharts',
                title='Hydrograph ',
                subtitle="Simulated and Observed flow for " + inputs_dictionary['simulation_name'],
                y_axis_title='Discharge',
                y_axis_units='cumecs',
                series=[{
                    'name': 'Simulated Flow',
                    'data': hydrograph_series,
                }]
            )




    context = {

        'test_function_response':test_function_response,
        "observed_hydrograph":observed_hydrograph,

        'simulation_name': simulation_name,
        'cell_size': cell_size,
        'timestep': timestep,
        'simulation_start_date_picker': simulation_start_date_picker,
        'simulation_end_date_picker': simulation_end_date_picker,
        'timeseries_source': timeseries_source,
        'threshold': threshold,
        'USGS_gage': USGS_gage,
        'model_engine': model_engine,
        'gage_id': id,
        'outlet_x': outlet_x, 'outlet_y': outlet_y,
        'box_topY': box_topY, 'box_rightX': box_rightX, 'box_leftX': box_leftX, 'box_bottomY': box_bottomY,
        'simulation_names_list': simulation_names_list,
        'existing_sim_res_id':existing_sim_res_id,
        'outlet_hs': outlet_hs,
        'bounding_box_hs': bounding_box_hs,

        'form_error': form_error,
        'validation_status': validation_status,
        'model_inputs_table_id':table_id,
        'geojson_outlet':geojson_outlet,
        'geojson_domain':geojson_files,

    }

    return render(request, 'hydrologic_modeling/model_input.html', context)


def model_run(request):
    """
    Controller that will display the run result (hydrograph). Also allows user to rerun model based on modifications
    """
    user_name = request.user.username

    # Defaults
    test_string = "Test_string_default"
    test_variable = "Test_variable_default"
    fac_L_form= ""
    simulation_name = ""
    outlet_y = ""
    outlet_x = ""

    hydrograph_series_obs = None
    hydrograph_series_sim = None
    hydrograph_opacity =0.2
    observed_hydrograph = ""
    observed_hydrograph2 = ''
    observed_hydrograph3 = ''

    observed_hydrograph_userModified = ""
    observed_hydrograph_userModified2 = ""
    observed_hydrograph_userModified3 = ""

    observed_hydrograph_loaded = ""
    observed_hydrograph_loaded2 = ""
    observed_hydrograph_loaded3 = ''

    eta_ts_obj = ''
    vo_ts_obj = ''
    vc_ts_obj = ""
    vs_ts_obj = ''

    model_run_hidden_form = ''
    hs_resource_id_created = ''
    simulation_loaded_id  = ""
    current_model_inputs_table_id = 0
    model_inputs_table_id_from_another_html = 0  #:TODO need to make it point to last sim by default
    # temp_folder = app_utils.generate_uuid_file_path()

    # if user wants to download the file only
    download_response = {}
    download_status = download_response['download_status'] = None #False
    download_link = download_response['download_link'] = 'http://link.to.zipped.files'
    hs_res_created = download_response['hs_res_created'] = '60hfg6060TRIAL6fgdf06dg'
    files_created_dict = 'No dict created'
    download_choice = None

    # gizmo settings
    fac_L = TextInput(display_text='fac_L', name='fac_L', initial=1.0)
    fac_Ks = TextInput(display_text='fac_Ks', name='fac_Ks', initial=1.0)
    fac_n_o = TextInput(display_text='fac_n_o', name='fac_n_o', initial=1.0)
    fac_n_c = TextInput(display_text='fac_n_c', name='fac_n_c', initial=1.0)
    fac_th_s = TextInput(display_text='fac_th_s', name='fac_th_s', initial=1.0)

    pvs_t0 = TextInput(display_text='pvs_t0', name='pvs_t0', initial=50.0)
    vo_t0 = TextInput(display_text='vo_t0', name='vo_t0', initial=10.0)
    qc_t0 = TextInput(display_text='qc_t0', name='qc_t0', initial=1.0)
    kc = TextInput(display_text='kc', name='kc', initial=1.0)

    # test
    if request.is_ajax and request.method == 'POST':
        pass


    # model_run can receive request from three sources:
    # 1) model_input, prepare model
    # 2) model_input, load model
    # 3) model_run, calibrate and change the result seen. i.e. passes to itself

    # check to see if the request is from method (1)
    try:
        model_input_prepare_request = request.POST['simulation_name']
        print "MSG: Preparing model simulation, simulation name is: ", model_input_prepare_request
    except:
        model_input_prepare_request = None


    # check to see if the request is from method (2)
    try:
        # for the input text
        try:
            model_input_load_request = hs_resource_id_created = request.POST['existing_sim_res_id']
            test_variable = str(hs_resource_id_created)
            print "MSG: Previous simulation is loaded.the simulation loaded from hs_res_id from text box is.", hs_resource_id_created

            # chose dropdown if the field is blank. :TODO need to get rid of the except part below:
            if hs_resource_id_created == "":
                model_input_load_request = hs_resource_id_created = request.POST['simulation_names_list']
                test_variable = str(hs_resource_id_created)+"______"
                print "MSG: Previous simulation is loaded. The name of simulation loaded is: ", hs_resource_id_created

        # for the drop down list
        except:
            model_input_load_request = hs_resource_id_created = request.POST['simulation_names_list'] #  from drop down menu
            b = request.POST['load_simulation_name']
            print 'MSG: The name of simulation loaded from dropdown menu is: ',hs_resource_id_created

            test_variable = str(hs_resource_id_created)+"______"+ str(b)
            print "MSG: Previous simulation is loaded. The name of simulation loaded is: ", hs_resource_id_created

    except:
        model_input_load_request = None


    # check to see if the request is from method (3)
    try:
        model_run_calib_request = request.POST['fac_L']
        print 'MSG: Calibration parameters are modified'
    except:
        model_run_calib_request = None


    # Method (1), request from model_input-prepare model
    if model_input_prepare_request != None:
        print 'MSG: Method I initiated.'

        # Checks the model chosen
        model_engine_chosen = request.POST['model_engine']

        if model_engine_chosen.lower() == 'topnet':
            test_string =  'TOPNET was chosen'
            print test_string

            inputs_dictionary = app_utils.create_model_input_dict_from_request(request)
            print inputs_dictionary
            run_request = app_utils.run_topnet(inputs_dictionary)

        elif model_engine_chosen.lower() == 'rhessys':
            test_string =  'RHESSys was chosen'
            print test_string
        else:
            # Check if user wants to just download the file
            try:
                download_choice = request.POST['download_choice']
                print '*********** download choice is ******', download_choice
                if download_choice == "geospatial":
                    print "Calling Geospatial function now!"

                    # validate  / return a confirmation to use regarding bounding box / input watershed

                    # creata input_dictionary from the request
                    inputs_dictionary = app_utils.create_model_input_dict_from_request(request)

                    # test_string = inputs_dictionary['cell_size']
                    # download_request_response = app_utils.download_geospatial_and_forcing_files(inputs_dictionary)
                    # if download_request_response != {}:
                    #     download_status = True
                    #     download_link = download_request_response
                elif download_choice == 'soil':
                    print "Downloading geospatial and soil file in progrress"
                    test_string ="Downloading geospatial and soil file in progrress"
                    inputs_dictionary = app_utils.create_model_input_dict_from_request(request)


                elif download_choice == 'forcing':
                    print "Downloading geospatial and forcing file in progrress"
                    test_string = "Downloading geospatial and forcing file in progrress"
                    inputs_dictionary = app_utils.create_model_input_dict_from_request(request)

                download_request_response = app_utils.download_geospatial_and_forcing_files(inputs_dictionary, download_request=download_choice)
                print "Downloading all the files successfully completed"
                if download_request_response != {}:
                    download_status = True
                    download_link = download_request_response

            except Exception, e:
                print 'The forcing file creation step gave error'
                f = file('/home/prasanna/Documents/error_log.html', 'w')
                f.write(str(e))
                f.close()

                if download_choice != None:
                    stop

                # # Method (1), STEP (1): get input dictionary from request ( request I)
                inputs_dictionary = app_utils.create_model_input_dict_from_request(request)
                test_string =  str("Prepared  Values: ")+str(inputs_dictionary)
                simulation_name = inputs_dictionary['simulation_name']
                print "MSG: Inputs from user read"

                # read shp. Not sure if this is needed
                try:
                    outlet_shp = request.FILES['outlet_shp']
                    watershed_upload = request.FILES['watershed_upload']

                    print "MSG: Shapefile from user read"
                except:
                    pass


                # # Method (1), STEP (2):call_runpytopkapi function

                ######### START: need to get two variables: i) hs_resource_id_created, and ii) hydrograph series ###############
                #response_JSON_file =  app_utils.call_runpytopkapi(inputs_dictionary= inputs_dictionary)
                response_JSON_file = '/home/prasanna/tethysdev/hydrologic_modeling/tethysapp/hydrologic_modeling/workspaces/user_workspaces/42240e0efd2148ec90c327a17530ee32/pytopkpai_responseJSON.txt'

                json_data = app_utils.read_data_from_json(response_JSON_file)

                hs_resource_id_created = json_data['hs_res_id_created']
                hydrograph_series_obs = json_data['hydrograph_series_obs']
                hydrograph_series_sim = json_data['hydrograph_series_sim']
                eta =  json_data['eta']
                vo = json_data['vo']
                vc = json_data['vc']
                vs = json_data['vs']

                print '*****************', hs_resource_id_created
                # print [i[-1] for i in hydrograph_series_sim]
                # hydrograph_series_obs = np.nan_to_num(hydrograph_series_obs).tolist()

                # replace nan values to 0 because Tethys timeseries cannot display nan
                hydrograph_series_obs = [[item[0], 0] if np.isnan(item[-1]) else item for item in hydrograph_series_obs]


                try:
                    # Writing to model_inputs_table
                    print '******************WARNING*********** Writing to database disabled'
                    # current_model_inputs_table_id = app_utils.write_to_model_input_table(inputs_dictionary=inputs_dictionary, hs_resource_id= hs_resource_id_created)
                    #
                    # # Writing to model_calibraiton_table (Because it is first record of the simulation)
                    # # IF the model did not run, or if user just wants the files, we don't write to calibration table
                    # current_model_calibration_table_id = app_utils.write_to_model_calibration_table( model_input_table_id=current_model_inputs_table_id)
                    #
                    # # Writing to model_result_table
                    # current_model_result_table_id = app_utils.write_to_model_result_table(model_calibration_table_id=current_model_calibration_table_id,
                    #                                                                       timeseries_discharge_list=hydrograph_series_sim)
                except Exception, e:
                    print "Error ---> Writing to DB"



                observed_hydrograph=  TimeSeries(
                    height='300px',width='500px', engine='highcharts',title=' Simulated Hydrograph ',
                    subtitle="Simulated and Observed flow  " ,
                    y_axis_title='Discharge',y_axis_units='cfs',
                    series=[{
                        'name': 'Simulated Flow',
                        'data': hydrograph_series_sim
                    }])

                observed_hydrograph2 = TimeSeries(
                    height='300px', width='500px', engine='highcharts', title=' Observed (Actual) Hydrograph ',
                    subtitle="Simulated and Observed flow  " ,
                    y_axis_title='Discharge', y_axis_units='cfs',
                    series=[
                            {'name': 'Observed Flow',
                             'data':  hydrograph_series_obs
                             }])

                observed_hydrograph3 = TimeSeries(
                    height='300px',
                    width='500px',
                    engine='highcharts',
                    title="Simulated and Observed flow  ",
                    y_axis_title='Discharge ',
                    y_axis_units='cfs',
                    series=[{
                        'name': 'Simulated Hydrograph',
                        'data': hydrograph_series_sim,
                        'fillOpacity': hydrograph_opacity,
                    }, {
                        'name': 'Observed Hydrograph',
                        'data': hydrograph_series_obs,
                        'fillOpacity': hydrograph_opacity,
                    }])

                eta_ts_obj =app_utils.create_1d(timeseries_list=eta, label='ETa', unit='mm/day')
                vc_ts_obj = app_utils.create_1d(timeseries_list=vc, label='Vc', unit='...')
                vs_ts_obj = app_utils.create_1d(timeseries_list=vs, label='Vs', unit='...')
                vo_ts_obj = app_utils.create_1d(timeseries_list=vo, label='Vo', unit='...')


    # Method (2), request from model_input-load simulation
    if model_input_load_request != None:
        hs_resource_id = model_input_load_request

        print 'MSG: Method II initiated.'
        print 'MSG: Model run for HydroShare resource ID ', hs_resource_id , " is being retreived.."


        # # STEP1: Retrieve simulation information (files stored in HydroShare) from db in a dict
        # inputs_dictionary = app_utils.create_model_input_dict_from_db( hs_resource_id= hs_resource_id,user_name= user_name )
        # test_string = str("Loaded  Values: ")+str(inputs_dictionary)



        ######### START: need to get two variables: i) hs_resource_id_created, and ii) hydrograph series ##############

        response_JSON_file =  app_utils.loadpytopkapi(hs_res_id=hs_resource_id, out_folder='')
        json_data = app_utils.read_data_from_json(response_JSON_file)

        hs_resource_id_created =hs_resource_id  #json_data['hs_res_id_created']
        print 'Showing results for ', hs_resource_id_created

        hydrograph_series_sim = json_data['hydrograph_series_sim']
        hydrograph_series_obs = json_data['hydrograph_series_obs']

        print '*****************', hs_resource_id_created
        print [i[-1] for i in hydrograph_series_sim]

        observed_hydrograph_loaded =  TimeSeries(
            height='500px',width='500px', engine='highcharts',title=' Simulated Hydrograph ',
            subtitle="Simulated and Observed flow  " ,
            y_axis_title='Discharge',y_axis_units='cfs',
            series=[{
                'name': 'Simulated Flow',
                'data':  hydrograph_series_sim
            }])

        observed_hydrograph_loaded2 =  TimeSeries(
            height='500px',width='500px', engine='highcharts',title='Observed (actual) Hydrograph ',
            subtitle="Simulated and Observed flow  " ,
            y_axis_title='Discharge',y_axis_units='cfs',
            series=[{
                'name': 'Simulated Flow',
                'data': hydrograph_series_obs
            }])

        observed_hydrograph_loaded3 = TimeSeries(
            height='500px',
            width='500px',
            engine='highcharts',
            title= "Simulated and Observed flow  " ,
            y_axis_title='Discharge (cfs)',
            y_axis_units='m',
            series=[{
                'name': 'Simulated Hydrograph',
                'data': hydrograph_series_sim,
                'fillOpacity': hydrograph_opacity,
            }, {
                'name': 'Observed Hydrograph',
                'data': hydrograph_series_obs,
                'fillOpacity': hydrograph_opacity,
            }]
        )





        # STEP2: Because in this part we load previous simulation, Load the model from hydroshare to hydroDS,
        # STEP2: And from the prepeared model, if the result is not available, run. Otherwise just give the result
        # hydrograph2, table_id = app_utils.run_model_with_input_as_dictionary(inputs_dictionary, False)
        #* STEP3: Make sure a string/variable/field remains that contains the id of the model. SO when user modifies it, that model is modifed
        # # STEP4B: Write to db
        # current_model_inputs_table_id = app_utils.write_to_model_input_table(inputs_dictionary,simulation_folder)
        # print "MSG: Inputs from model_input form written to db. Model RAN already"
        # STEP5: get the revised hydrographs, and plot it
        # preparing timeseries data in the format shown in: http://docs.tethysplatform.org/en/latest/tethys_sdk/gizmos/plot_view.html#time-series

        # hydrograph2 = []
        # observed_hydrograph_loaded = ''



    # Method (3), request from model_run, change calibration parameters
    if model_run_calib_request != None :

        fac_L_form = float(request.POST['fac_L'])
        fac_Ks_form = float(request.POST['fac_Ks'])
        fac_n_o_form = float(request.POST['fac_n_o'])
        fac_n_c_form = float(request.POST['fac_n_c'])
        fac_th_s_form = float(request.POST['fac_th_s'])

        pvs_t0_form = float(request.POST['pvs_t0'])
        vo_t0_form = float(request.POST['vo_t0'])
        qc_t0_form = float(request.POST['qc_t0'])
        kc_form = float(request.POST['kc'])

        # model_inputs_table_id_from_another_html = request.POST['model_inputs_table_id_from_another_html']
        hs_resource_id_from_previous_simulation = request.POST['model_inputs_table_id_from_another_html']
        # current_model_inputs_table_id  =hs_resource_id_from_previous_simulation
        hs_resource_id_created = hs_resource_id_from_previous_simulation

        print 'MSG: Method III initiated. The model id we are looking at is: ', hs_resource_id_from_previous_simulation


        ######### START: need to get two variables: i) hs_resource_id_created, and ii) hydrograph series ###############
        response_JSON_file =  app_utils.modifypytopkapi(hs_res_id=hs_resource_id_created, out_folder='',
                                                        fac_l=fac_L_form, fac_ks=fac_Ks_form, fac_n_o=fac_n_o_form,
                                                        fac_n_c=fac_n_c_form, fac_th_s=fac_th_s_form,
                                                        pvs_t0=pvs_t0_form, vo_t0=vo_t0_form, qc_t0=qc_t0_form,
                                                        kc=kc_form )

        json_data = app_utils.read_data_from_json(response_JSON_file)

        hs_resource_id_created =  hs_resource_id_created # json_data['hs_res_id_created']
        hydrograph_series_sim = json_data['hydrograph_series_sim']
        hydrograph_series_obs = json_data['hydrograph_series_obs']

        print '*****************', hs_resource_id_created
        print [i[-1] for i in hydrograph_series_sim]
        ######### END :  ###############

        # # # -------DATABASE STUFFS  <start>----- # #
        # # retreive the model_inputs_table.id of this entry to pass it to the next page (calibration page)
        # from .model import engine, SessionMaker, Base, model_calibration_table
        # session = SessionMaker()                # Make session
        #
        # # STEP1: retrieve the model_inputs_table.id of this entry to pass it to the next page (calibration page)
        # current_model_inputs_table_id = str(len(session.query(model_inputs_table).filter(
        #                                             model_inputs_table.user_name == user_name).all()))  # because PK is the same as no of rows, i.e. length
        #
        # # STEP2: use the id retrieved in STEP1 to get all the remaining parameters
        # print 'model_input ID for which rest of the inputs are being retrieved: ', current_model_inputs_table_id
        #
        # all_rows = session.query(model_inputs_table).filter(model_inputs_table.id == current_model_inputs_table_id).all()
        #
        # # retrieve the parameters and write to a dictionary
        # inputs_dictionary = {}
        #
        # for row in all_rows:
        #     inputs_dictionary['id'] = row.id
        #     inputs_dictionary['user_name'] = row.user_name
        #     inputs_dictionary['simulation_name'] = row.simulation_name
        #     inputs_dictionary['simulation_folder'] = row.simulation_folder
        #     inputs_dictionary['simulation_start_date'] = row.simulation_start_date
        #     inputs_dictionary['simulation_end_date'] = row.simulation_end_date
        #     inputs_dictionary['USGS_gage'] = row.USGS_gage
        #
        #     inputs_dictionary['outlet_x'] = row.outlet_x
        #     inputs_dictionary['outlet_y'] = row.outlet_y
        #     inputs_dictionary['box_topY'] = row.box_topY
        #     inputs_dictionary['box_bottomY'] = row.box_bottomY
        #     inputs_dictionary['box_rightX'] = row.box_rightX
        #     inputs_dictionary['box_leftX'] = row.box_leftX
        #
        #     timeseries_source,threshold, cell_size,timestep =  row.other_model_parameters.split("__")
        #     inputs_dictionary['timeseries_source'] = timeseries_source
        #     inputs_dictionary['threshold'] = threshold
        #     inputs_dictionary['cell_size'] = cell_size
        #     inputs_dictionary['timestep'] = timestep
        #
        #     inputs_dictionary['model_engine'] = row.model_engine



        observed_hydrograph_userModified = TimeSeries(
            height='500px',
            width='500px',
            engine='highcharts',
            title=' Corrected Hydrograph ',
            subtitle="Simulated and Observed flow " ,
            y_axis_title='Discharge',
            y_axis_units='cfs',
            series=[{
                'name': 'Simulated Flow',
                'data': hydrograph_series_sim
            }]
        )

        observed_hydrograph_userModified2 = TimeSeries(
            height='500px', width='500px', engine='highcharts', title=' Observed (Actual) Hydrograph ',
            subtitle="Simulated and Observed flow " ,
            y_axis_title='Discharge', y_axis_units='cfs',
            series=[{
                'name': 'Observed Flow',
                'data': hydrograph_series_obs
            }])

        observed_hydrograph_userModified3 = TimeSeries(
            height='500px',
            width='500px',
            engine='highcharts',
            title= "Simulated and Observed flow " ,
            y_axis_title='Discharge ',
            y_axis_units='cfs',
            series=[{
                'name': 'Simulated Hydrograph',
                'data': hydrograph_series_sim
            }, {
                'name': 'Observed Hydrograph',
                'data': hydrograph_series_obs
            }]
        )

        # create input_dictionary for the last run. Because we are modifying, we need to load the last run
        inputs_dictionary = app_utils.create_model_input_dict_from_db(hs_resource_id = hs_resource_id_from_previous_simulation, user_name= user_name )

        # print 'MSG: Input Dictionary from db of model_input_id= ', model_inputs_table_id_from_another_html, " created for simulation: ", inputs_dictionary['simulation_name']
        test_string = str(inputs_dictionary)
        test_variable = hs_resource_id_from_previous_simulation


        # following two line should replace the above lines for querring db
        # from .model import model_inputs_table, model_calibration_table


        # # STEP6: write the calibration and numerical parameters to the database
        # calibrated_model_info = model_calibration_table(current_model_inputs_table_id, fac_L_form, fac_Ks_form,
        #                                                 fac_n_o_form, fac_n_c_form, fac_th_s_form,
        #                                                 pvs_t0_form, vo_t0_form, qc_t0_form,
        #                                                 kc_form)  # 1 in the begenning is for model_run id, pk for model run
        # session.add(calibrated_model_info)
        # session.commit()
        # # # -------DATABASE STUFFS  <ends> ----- # #

    context = {'simulation_name':simulation_name,
               'outlet_y': outlet_y,
               'outlet_x': outlet_x,


               'fac_L': fac_L, 'fac_Ks': fac_Ks, 'fac_n_o': fac_n_o, "fac_n_c": fac_n_c, "fac_th_s": fac_th_s,
               'pvs_t0': pvs_t0,  'vo_t0': vo_t0, 'qc_t0': qc_t0,   "kc": kc,

               'fac_L_form': fac_L_form,
               'user_name':user_name,

               #'Iwillgiveyou_model_inputs_table_id_from_another_html':model_inputs_table_id_from_another_html,
               # "current_model_inputs_table_id":current_model_inputs_table_id, # model_inputs_table_id

               'observed_hydrograph': observed_hydrograph,
               'observed_hydrograph3': observed_hydrograph3,
               'observed_hydrograph2': observed_hydrograph2,


               "observed_hydrograph_userModified":observed_hydrograph_userModified,
               "observed_hydrograph_userModified2": observed_hydrograph_userModified2,
               "observed_hydrograph_userModified3": observed_hydrograph_userModified3,

               "observed_hydrograph_loaded":observed_hydrograph_loaded,
               "observed_hydrograph_loaded2": observed_hydrograph_loaded2,
               "observed_hydrograph_loaded3": observed_hydrograph_loaded3,

               'eta_ts_obj': eta_ts_obj,
               'vs_ts_obj': vs_ts_obj,
               'vc_ts_obj': vc_ts_obj,
               'vo_ts_obj': vo_ts_obj,

               #"simulation_loaded_id":simulation_loaded_id,
               'test_string':str(type(observed_hydrograph)), #test_string
               'test_variable':test_variable,
               'hs_resource_id_created':hs_resource_id_created,

                # fow download request
               'download_status': download_status,
               'download_link': download_link,
               'hs_res_created': hs_res_created,
               'dict_files_created': files_created_dict,
               }

    return render(request, 'hydrologic_modeling/model-run.html', context)




def download_request(request):

    # defaults values
    download_response = {}
    download_status = download_response['download_status'] = False
    download_link = download_response['download_link'] = 'http://link.to.zipped.files'
    hs_res_created = download_response['hs_res_created'] = '60hfg60606fgdf06dg'
    files_created_dict = 'No dict created'
    # validate  / return a confirmation to use regarding bounding box / input watershed

    # creata input_dictionary from the request

    inputs_dictionary = app_utils.create_model_input_dict_from_request(request)
    test_string = inputs_dictionary['cell_size']
    # resource ID to file created, as well as links to files created
    # files_created_dict =  app_utils.download_geospatial_and_forcing_files(inputs_dictionary)

    context = { 'download_status': download_status,
                'download_link':download_link,
                'hs_res_created':hs_res_created,
                'dict_files_created':files_created_dict,
                'test_string':test_string,
               }
    print "this function has been called!"
    return render(request, 'hydrologic_modeling/download_request.html', context)








def visualize_shp(request):
    # when it receives request. This is not in effect. Currently, the request is sent to model_run, not model_input.html
    geojson_files = {}
    if request.is_ajax and request.method == 'POST':
        print "Request Received"

        for afile in request.FILES.getlist('watershed_upload'):

            if afile.name.split(".")[-1] == "shp":
                watershed_upload = afile
            if afile.name.split(".")[-1] == "shx":
                watershed_shx = afile
            if afile.name.split(".")[-1] == "prj":
                watershed_prj = afile
            if afile.name.split(".")[-1] == "dbf":
                watershed_dbf = afile



        # lines below are not being executed
        # box_rightX, box_bottomY, box_leftX, box_topY = get_box_xyxy_from_shp_shx(shp_file=watershed_upload,shx_file=watershed_shx)
        geojson_files['geojson_domain'] = app_utils.shapefile_to_geojson(watershed_upload)
        print geojson_files

        # validation_status, form_error, inputs_dictionary, geojson_files = app_utils.validate_inputs(request) # input_dictionary has proper data type. Not everything string

        for geojson in geojson_files.keys():
            if geojson == 'geojson_outlet':
                geojson_outlet = geojson_files['geojson_outlet']
                print geojson_outlet
            if geojson == 'geojson_domain':
                geojson_domain = geojson_files['geojson_domain']
                print geojson_domain



    context = {

        'geojson_file':geojson_domain
    }

    render(request, 'hydrologic_modeling/model_input.html', context)

    return


def google_map_input(request):

    context = {}
    return render(request, 'hydrologic_modeling/googlemap.html', context)



def test2(request):
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from django.conf import settings

    test_string = 'None'
    wshed_shp_fname = None
    outlet_shp_fname = None

    watershed_files = {}
    outlet_files = {}

    cell_size = 300
    avg_lat = 40 # (inputs_dictionary['box_bottomY'] + inputs_dictionary['box_topY'])/2

    if request.is_ajax and request.method == 'POST' and request.FILES.getlist('watershed_upload') != []:

        for afile in request.FILES.getlist('watershed_upload'):

            print "watershed file(s) detected"

            tmp = os.path.join(settings.MEDIA_ROOT, "tmp", afile.name)
            path = default_storage.save(tmp, ContentFile(afile.read()))

            tmp_file = os.path.join(settings.MEDIA_ROOT, path)
            tmp_file = os.path.abspath(tmp_file)
            if os.path.split(tmp_file)[-1].split(".")[-1] == 'shp':
                watershed_files['shp'] = tmp_file
            if os.path.split(tmp_file)[-1].split(".")[-1] == 'shx':
                watershed_files['shx'] = tmp_file
            if os.path.split(tmp_file)[-1].split(".")[-1] == 'dbf':
                watershed_files['dbf'] = tmp_file
            if os.path.split(tmp_file)[-1].split(".")[-1] == 'prj':
                watershed_files['prj'] = tmp_file
            if os.path.split(tmp_file)[-1].split(".")[-1] =='tif' or os.path.split(tmp_file)[-1].split(".")[-1]=='tiff':
                watershed_files['tif'] = tmp_file
            if os.path.split(tmp_file)[-1][-3:] not in ['shp', 'shx', 'dbf', 'prj', 'tif', 'iff']:
                os.remove(tmp_file)

        if 'shp' and 'shx' in watershed_files:
            wshed_shp_fname = app_utils.rename_shapefile_collection(watershed_files, 'watershed')

    if request.is_ajax and request.method == 'POST' and request.FILES.getlist('outlet_upload') != []:

        print "Outlet file(s) detected", request.FILES.getlist('outlet_upload')

        for afile in request.FILES.getlist('outlet_upload'):

            tmp = os.path.join(settings.MEDIA_ROOT, "tmp", afile.name)
            path = default_storage.save(tmp, ContentFile(afile.read()))

            tmp_file = os.path.join(settings.MEDIA_ROOT, path)
            tmp_file = os.path.abspath(tmp_file)
            if os.path.split(tmp_file)[-1].split(".")[-1] == 'shp':
                outlet_files['shp'] = tmp_file
            if os.path.split(tmp_file)[-1].split(".")[-1] == 'shx':
                outlet_files['shx'] = tmp_file
            if os.path.split(tmp_file)[-1].split(".")[-1] == 'dbf':
                outlet_files['dbf'] = tmp_file
            if os.path.split(tmp_file)[-1].split(".")[-1] == 'prj':
                outlet_files['prj'] = tmp_file
            if os.path.split(tmp_file)[-1].split(".")[-1] =='tif' or os.path.split(tmp_file)[-1].split(".")[-1]=='tiff':
                outlet_files['tif'] = tmp_file
            if os.path.split(tmp_file)[-1][-3:] not in ['shp', 'shx', 'dbf', 'prj', 'tif', 'tiff']:
                os.remove(tmp_file)

        outlet_shp_fname = app_utils.rename_shapefile_collection(outlet_files, 'outlet')

    if wshed_shp_fname != None:

        # get the bounding box
        lon_e, lat_s, lon_w, lat_n = app_utils.get_box_xyxy_from_shp(wshed_shp_fname+'.shp')

        # bbox with buffer (3 * cell size)
        angle_along_lon, angle_along_lat = app_utils.meter_to_degree(cell_size, avg_lat)
        lon_e, lat_s, lon_w, lat_n = lon_e+angle_along_lon, lat_s-angle_along_lat, lon_w-angle_along_lon, lat_n+angle_along_lat

        # convert to watershed geojson
        geojson_fullpath = os.path.abspath(app_utils.shapefile_to_geojson(wshed_shp_fname+'.shp'))
        test_string =  'Watershed shapefile detected. Converted to geojson at'+ geojson_fullpath

    if outlet_shp_fname != None:
        # get the outlet coordinate
        lon, lat = app_utils.get_outlet_xy_from_shp(outlet_shp_fname+'.shp')

        # covert to geojson
        geojson_fullpath = os.path.abspath( app_utils.shapefile_to_geojson(outlet_shp_fname+'.shp') )
        test_string = test_string +  'Outlet shapefile detected. Converted to geojson at'+ geojson_fullpath

    if 'tif' in  watershed_files:
        lon_e, lat_s, lon_w, lat_n = app_utils.get_box_from_tif(watershed_files['tif'])



    import datetime

    hydrograph_series_sim = [[datetime.datetime(2010, 10, 2, 0, 0), 0.0], [datetime.datetime(2010, 10, 3, 0, 0), 1.113],
                [datetime.datetime(2010, 10, 4, 0, 0), 1.17], [datetime.datetime(2010, 10, 5, 0, 0), 1.356],
                [datetime.datetime(2010, 10, 6, 0, 0), 1.918], [datetime.datetime(2010, 10, 7, 0, 0), 0.0],
                [datetime.datetime(2010, 10, 8, 0, 0), 0.0], [datetime.datetime(2010, 10, 9, 0, 0), 0.0],
                [datetime.datetime(2010, 10, 10, 0, 0), 0.161], [datetime.datetime(2010, 10, 11, 0, 0), 2.627],
                [datetime.datetime(2010, 10, 12, 0, 0), 8.327], [datetime.datetime(2010, 10, 13, 0, 0), 43.355],
                [datetime.datetime(2010, 10, 14, 0, 0), 0.0], [datetime.datetime(2010, 10, 15, 0, 0), 0.0],
                [datetime.datetime(2010, 10, 16, 0, 0), 0.0], [datetime.datetime(2010, 10, 17, 0, 0), 1.0],
                [datetime.datetime(2010, 10, 18, 0, 0), 1.178], [datetime.datetime(2010, 10, 19, 0, 0), 1.577],
                [datetime.datetime(2010, 10, 20, 0, 0), 4.973], [datetime.datetime(2010, 10, 21, 0, 0), 8.108],
                [datetime.datetime(2010, 10, 22, 0, 0), 0.0], [datetime.datetime(2010, 10, 23, 0, 0), 0.0],
                [datetime.datetime(2010, 10, 24, 0, 0), 1.058], [datetime.datetime(2010, 10, 25, 0, 0), 20.553],
                [datetime.datetime(2010, 10, 26, 0, 0), 17.641], [datetime.datetime(2010, 10, 27, 0, 0), 5.0],
                [datetime.datetime(2010, 10, 28, 0, 0), 2.0], [datetime.datetime(2010, 10, 29, 0, 0), 0.0],
                [datetime.datetime(2010, 10, 30, 0, 0), 0.0], [datetime.datetime(2010, 10, 31, 0, 0), 1.122]]
    hydrograph_series_obs = [[datetime.datetime(2010, 10, 2, 0, 0), 0.0], [datetime.datetime(2010, 10, 3, 0, 0), 0.113],
                [datetime.datetime(2010, 10, 4, 0, 0), 0.17], [datetime.datetime(2010, 10, 5, 0, 0), 0.356],
                [datetime.datetime(2010, 10, 6, 0, 0), 0.918], [datetime.datetime(2010, 10, 7, 0, 0), 0.0],
                [datetime.datetime(2010, 10, 8, 0, 0), 0.0], [datetime.datetime(2010, 10, 9, 0, 0), 0.0],
                [datetime.datetime(2010, 10, 10, 0, 0), 0.161], [datetime.datetime(2010, 10, 11, 0, 0), 2.627],
                [datetime.datetime(2010, 10, 12, 0, 0), 8.327], [datetime.datetime(2010, 10, 13, 0, 0), 13.355],
                [datetime.datetime(2010, 10, 14, 0, 0), 0.0], [datetime.datetime(2010, 10, 15, 0, 0), 0.0],
                [datetime.datetime(2010, 10, 16, 0, 0), 0.0], [datetime.datetime(2010, 10, 17, 0, 0), 0.0],
                [datetime.datetime(2010, 10, 18, 0, 0), 0.178], [datetime.datetime(2010, 10, 19, 0, 0), 1.577],
                [datetime.datetime(2010, 10, 20, 0, 0), 4.973], [datetime.datetime(2010, 10, 21, 0, 0), 8.108],
                [datetime.datetime(2010, 10, 22, 0, 0), 0.0], [datetime.datetime(2010, 10, 23, 0, 0), 0.0],
                [datetime.datetime(2010, 10, 24, 0, 0), 1.058], [datetime.datetime(2010, 10, 25, 0, 0), 6.553],
                [datetime.datetime(2010, 10, 26, 0, 0), 17.641], [datetime.datetime(2010, 10, 27, 0, 0), 0.0],
                [datetime.datetime(2010, 10, 28, 0, 0), 0.0], [datetime.datetime(2010, 10, 29, 0, 0), 0.0],
                [datetime.datetime(2010, 10, 30, 0, 0), 0.0], [datetime.datetime(2010, 10, 31, 0, 0), 1.122]]


    # json_data = app_utils.read_data_from_json('/home/prasanna/tethysdev/hydrologic_modeling/tethysapp/hydrologic_modeling/workspaces/user_workspaces/598d95d552804c188e721a7762611399/output_response_txt.txt')
    #
    # hydrograph_series_obs2 = json_data['hydrograph_series_obs']
    # hydrograph_series_sim2 = json_data['hydrograph_series_sim']


    observed_hydrograph = TimeSeries(
        height='500px', width='500px', engine='highcharts', title=' Simulated Hydrograph ',
        subtitle="Simulated and Observed flow for " ,
        y_axis_title='Discharge', y_axis_units='cfs',
        series=[{
            'name': 'Simulated Flow',
            'data': hydrograph_series_sim
        }])

    observed_hydrograph2 = TimeSeries(
        height='500px', width='500px', engine='highcharts', title=' Observed (Actual) Hydrograph ',
        subtitle="Simulated and Observed flow for " ,
        y_axis_title='Discharge', y_axis_units='cfs',
        series=[
            {'name': 'Observed Flow',
             'data': hydrograph_series_obs
             }
        ]
    )

    # hydrograp_obj = AreaRange(
    #     title='Hydrograph',
    #     y_axis_title='cfs',
    #     y_axis_units='cfs',
    #     series=[{
    #         'name': 'series_1 Flow',
    #         'data': hydrograph_series_sim,
    #         'zIndex': 1,
    #         'marker': {
    #             'lineWidth': 2,
    #         }
    #     }, {
    #         'name': 'series_2 Flow',
    #         'data': hydrograph_series_obs,
    #         'type': 'arearange',
    #         'lineWidth': 0.1,
    #         'linkedTo': ':previous',
    #         'fillOpacity': 0.3,
    #         'zIndex': 0
    #     }]
    # )
    # areaPlot = PlotView(plot_object=hydrograp_obj,
    #                                 width='500px',
    #                                 height='500px')
    #





    # # print hydrograph_series_sim2
    # print "*******************************"
    # print "NOT working data type= ",type(hydrograph_series_obs2[0][0]), ' One such value=',  hydrograph_series_obs2[1], ' And the lenght=',  len(hydrograph_series_obs2),len(hydrograph_series_sim2)
    # # multi_timeseries_plot = app_utils.plot_multiseries_hydrograph(obs_q=hydrograph_series_obs2, sim_q=hydrograph_series_sim2)

    print "YES working data type= ",type(hydrograph_series_obs[0][0]), ' One such value=',  hydrograph_series_obs[0], ' And the lenght=',  len(hydrograph_series_obs),len(hydrograph_series_sim)
    # print hydrograph_series_obs
    multi_timeseries_plot = TimeSeries(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Multiple Timeseries Plot',
        y_axis_title='Snow depth',
        y_axis_units='m',
        series=[{
            'name': 'Simulated Hydrograph',
            'data': hydrograph_series_sim ,
            # 'color': 'lightblue',
            'fillOpacity': 0.2,
        }, {
            'name': 'Observed Hydrographhh',
            'data': hydrograph_series_obs,
            'fillOpacity': 0.2,
            # 'color':'lightgrey'
        }]
    )














    context = {
                'test_string1':test_string,
        # 'area_range_plot_object':areaPlot,
        'observed_hydrograph':observed_hydrograph,
        'observed_hydrograph2': observed_hydrograph2,

        # 'timeseries_plot': timeseries_plot,
        'multi_timeseries_plot': multi_timeseries_plot,
        # 'area_range_plot': area_range_plot,


    }
    return render(request, 'hydrologic_modeling/test2.html', context)


def model_input0(request): # for a URL with variables in it, the variables need to be added to the arguments of the controller function it maps to
    """
    Controller for ..........
    """

    user_name = request.user.username

    # # DROP DOWN LIST---- query existing simulation records. Put them in drop down --------- # #
    from .model import engine, SessionMaker, Base, model_inputs_table, model_calibration_table
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

    simulation_names_list = SelectInput(display_text='Load Saved Simulations',
                                     name='simulation_names_list',
                                     multiple=False,
                                     options=  queries )
    # # -------------------------------- querying ---------------------------------------- # #




    # Define Gizmo Options
    simulation_name = TextInput(display_text='Simulation name', name='simulation_name', initial='simulation-1')
    USGS_gage = TextInput(display_text='USGS gage number close to the outlet', name='USGS_gage', initial='10172200')
    cell_size = TextInput(display_text='Cell size in meters', name='cell_size', initial='100')
    timestep = TextInput(display_text='Timestep in hrs', name='timestep', initial='6') #, append="hours"
    simulation_start_date_picker = DatePicker(name='simulation_start_date_picker', display_text='Start Date',
                                              autoclose=True, format='mm-dd-yyyy', start_date='01/01/2011',
                                              start_view='month', today_button=True, initial='01/01/2014')
    simulation_end_date_picker = DatePicker(name='simulation_end_date_picker', display_text='Start Date',
                                            autoclose=True, format='mm-dd-yyyy', start_date='01/01/2011',
                                            start_view='month', today_button=True, initial='06/30/2014')

    timeseries_source = SelectInput(display_text='Timeseries source',
                name='timeseries_source',
                multiple=False,
                options=[('User File', 'user_file'), ('UEB', 'UEB'), ('Daymet', 'Daymet')],
                initial=['User File'],
                original=['User File'])

    model_engine = SelectInput(display_text='Choose Model',
                name='model_engine',
                multiple=False,
                options=[('TOPKAPI', 'TOPKAPI'), ('TOPNET', 'TOPNET'), ('RHESSys', 'RHESSys')],
                initial=['TOPKAPI'],
                original=['TOPKAPI'])

    threshold = TextInput(display_text='Threshold', name='threshold', initial='25')

    # html form to django form
    outlet_x = TextInput(display_text='', name='outlet_x', initial='-111.7915')
    outlet_y = TextInput(display_text='', name='outlet_y', initial=' 41.74025')

    box_topY = TextInput(display_text='North Y', name='box_topY', initial='41.7215')
    box_rightX = TextInput(display_text='East X', name='box_rightX', initial='-111.8461 ')
    box_leftX = TextInput(display_text='West X', name='box_leftX', initial='-111.6208')
    box_bottomY = TextInput(display_text='South Y', name='box_bottomY', initial='41.88')

    # Create template context dictionary
    context = {'simulation_name': simulation_name,
               'cell_size': cell_size,
               'timestep': timestep,
               'simulation_start_date_picker': simulation_start_date_picker,
               'simulation_end_date_picker': simulation_end_date_picker,
               'timeseries_source': timeseries_source,
               'threshold': threshold,
               'USGS_gage': USGS_gage,

               'model_engine':model_engine,
               'gage_id': id,
                'simulation_names_list':simulation_names_list,
               'outlet_x':outlet_x, 'outlet_y':outlet_y,
               'box_topY': box_topY,  'box_rightX': box_rightX,  'box_leftX': box_leftX,  'box_bottomY': box_bottomY,
                }
    return render(request, 'hydrologic_modeling/model-input0.html', context)


def model_input2(request): # for a URL with variables in it, the variables need to be added to the arguments of the controller function it maps to
    """
    Controller for ..........
    """

    user_name = request.user.username

    # Define Gizmo Options
    from .model import engine, SessionMaker, Base, model_inputs_table, model_calibration_table
    simulation_names_list = "" # create_simulation_list_after_querying_db(user_name)

    simulation_name = TextInput(display_text='Simulation name', name='simulation_name', initial='simulation-1')
    USGS_gage = TextInput(display_text='USGS gage nearby', name='USGS_gage', initial='10172200')
    cell_size = TextInput(display_text='Cell size in meters', name='cell_size', initial='100')
    timestep = TextInput(display_text='Timestep in hrs', name='timestep', initial='6') #, append="hours"
    simulation_start_date_picker = DatePicker(name='simulation_start_date_picker', display_text='Start Date',
                                              autoclose=True, format='mm-dd-yyyy', start_date='01/01/2011',
                                              start_view='month', today_button=True, initial='01/01/2014')
    simulation_end_date_picker = DatePicker(name='simulation_end_date_picker', display_text='End Date',
                                            autoclose=True, format='mm-dd-yyyy', start_date='01/01/2011',
                                            start_view='month', today_button=True, initial='06/30/2014')

    timeseries_source = SelectInput(display_text='Timeseries source',
                name='timeseries_source',
                multiple=False,
                options=[('User File', 'user_file'), ('UEB', 'UEB'), ('Daymet', 'Daymet')],
                initial=['User File'],
                original=['User File'])

    model_engine = SelectInput(display_text='Choose Model',
                name='model_engine',
                multiple=False,
                options=[('TOPKAPI', 'TOPKAPI'), ('TOPNET', 'TOPNET'), ('RHESSys', 'RHESSys')],
                initial=['TOPKAPI'],
                original=['TOPKAPI'])

    threshold = TextInput(display_text='Stream threshold', name='threshold', initial='25')

    # html form to django form
    outlet_x = TextInput(display_text='Longitude', name='outlet_x', initial='-111.7915')
    outlet_y = TextInput(display_text='Latitude', name='outlet_y', initial=' 41.74025')

    box_topY = TextInput(display_text='North Y', name='box_topY', initial='41.7215')
    box_rightX = TextInput(display_text='East X', name='box_rightX', initial='-111.8461')
    box_leftX = TextInput(display_text='West X', name='box_leftX', initial='-111.6208')
    box_bottomY = TextInput(display_text='South Y', name='box_bottomY', initial='41.88')

    outlet_hs = TextInput(display_text='', name='outlet_hs', initial='')
    bounding_box_hs = TextInput(display_text='', name='bounding_box_hs', initial='')





    # Create template context dictionary
    context = {'simulation_name': simulation_name,
               'cell_size': cell_size,
               'timestep': timestep,
               'simulation_start_date_picker': simulation_start_date_picker,
               'simulation_end_date_picker': simulation_end_date_picker,
               'timeseries_source': timeseries_source,
               'threshold': threshold,
               'USGS_gage': USGS_gage,

               'model_engine':model_engine,
               'gage_id': id,
               'outlet_x':outlet_x, 'outlet_y':outlet_y,
               'box_topY': box_topY,  'box_rightX': box_rightX,  'box_leftX': box_leftX,  'box_bottomY': box_bottomY,
               'simulation_names_list':simulation_names_list,
               'outlet_hs':outlet_hs,
               'bounding_box_hs': bounding_box_hs,
               }

    return render(request, 'hydrologic_modeling/model-input2.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import AreaRange, TimeSeries



@login_required()
def test3(request):
    from datetime import datetime
    """
    Controller for the app home page.
    """
    # TIMESERIES PLOT (HIGHCHARTS)
    ts_data1 = [[datetime(2008, 12, 2), 0.8], [datetime(2008, 12, 9), 0.6], [datetime(2008, 12, 16), 0.6],
                [datetime(2008, 12, 28), 0.67], [datetime(2009, 1, 1), 0.81], [datetime(2009, 1, 8), 0.78],
                [datetime(2009, 1, 12), 0.98], [datetime(2009, 1, 27), 1.84], [datetime(2009, 2, 10), 1.80],
                [datetime(2009, 2, 18), 1.80], [datetime(2009, 2, 24), 1.92], [datetime(2009, 3, 4), 2.49],
                [datetime(2009, 3, 11), 2.79], [datetime(2009, 3, 15), 2.73], [datetime(2009, 3, 25), 2.61],
                [datetime(2009, 4, 2), 2.76], [datetime(2009, 4, 6), 2.82], [datetime(2009, 4, 13), 2.8],
                [datetime(2009, 5, 3), 2.1], [datetime(2009, 5, 26), 1.1], [datetime(2009, 6, 9), 0.25],
                [datetime(2009, 6, 12), 0]]

    timeseries_plot = TimeSeries(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Single Timeseries Plot',
        y_axis_title='Snow depth',
        y_axis_units='m',
        series=[{
            'name': 'Winter 2007-2008',
            'data': ts_data1
        }]
    )

    # MULTIPLE TIMESERIES ON ONE PLOT (HIGHCHARTS)
    ts_data2 = [[datetime(2008, 12, 2), 1.8], [datetime(2008, 12, 9), 1.6], [datetime(2008, 12, 16), 1.6],
                [datetime(2008, 12, 28), 1.67], [datetime(2009, 1, 1), 1.81], [datetime(2009, 1, 8), 1.78],
                [datetime(2009, 1, 12), 1.98], [datetime(2009, 1, 27), 2.84], [datetime(2009, 2, 10), 2.80],
                [datetime(2009, 2, 18), 2.80], [datetime(2009, 2, 24), 2.92], [datetime(2009, 3, 4), 3.49],
                [datetime(2009, 3, 11), 3.79], [datetime(2009, 3, 15), 3.73], [datetime(2009, 3, 25), 3.61],
                [datetime(2009, 4, 2), 3.76], [datetime(2009, 4, 6), 3.82], [datetime(2009, 4, 13), 3.8],
                [datetime(2009, 5, 3), 3.1], [datetime(2009, 5, 26), 2.1], [datetime(2009, 6, 9), 1.25],
                [datetime(2009, 6, 12), 1]]

    multi_timeseries_plot = TimeSeries(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Multiple Timeseries Plot',
        y_axis_title='Snow depth',
        y_axis_units='m',
        series=[{
            'name': 'Winter 2007-2008 (1)',
            'data': ts_data2  # I switched these so that the shorter series was in front of the larger
        }, {
            'name': 'Winter 2007-2008 (2)',
            'data': ts_data1
        }]
    )

    averages = [
        [datetime(2009, 7, 1), 21.5], [datetime(2009, 7, 2), 22.1], [datetime(2009, 7, 3), 23],
        [datetime(2009, 7, 4), 23.8], [datetime(2009, 7, 5), 21.4], [datetime(2009, 7, 6), 21.3],
        [datetime(2009, 7, 7), 18.3], [datetime(2009, 7, 8), 15.4], [datetime(2009, 7, 9), 16.4],
        [datetime(2009, 7, 10), 17.7], [datetime(2009, 7, 11), 17.5], [datetime(2009, 7, 12), 17.6],
        [datetime(2009, 7, 13), 17.7], [datetime(2009, 7, 14), 16.8], [datetime(2009, 7, 15), 17.7],
        [datetime(2009, 7, 16), 16.3], [datetime(2009, 7, 17), 17.8], [datetime(2009, 7, 18), 18.1],
        [datetime(2009, 7, 19), 17.2], [datetime(2009, 7, 20), 14.4],
        [datetime(2009, 7, 21), 13.7], [datetime(2009, 7, 22), 15.7], [datetime(2009, 7, 23), 14.6],
        [datetime(2009, 7, 24), 15.3], [datetime(2009, 7, 25), 15.3], [datetime(2009, 7, 26), 15.8],
        [datetime(2009, 7, 27), 15.2], [datetime(2009, 7, 28), 14.8], [datetime(2009, 7, 29), 14.4],
        [datetime(2009, 7, 30), 15], [datetime(2009, 7, 31), 13.6]
    ]

    ranges = [
        [datetime(2009, 7, 1), 14.3, 27.7], [datetime(2009, 7, 2), 14.5, 27.8], [datetime(2009, 7, 3), 15.5, 29.6],
        [datetime(2009, 7, 4), 16.7, 30.7], [datetime(2009, 7, 5), 16.5, 25.0], [datetime(2009, 7, 6), 17.8, 25.7],
        [datetime(2009, 7, 7), 13.5, 24.8], [datetime(2009, 7, 8), 10.5, 21.4], [datetime(2009, 7, 9), 9.2, 23.8],
        [datetime(2009, 7, 10), 11.6, 21.8], [datetime(2009, 7, 11), 10.7, 23.7], [datetime(2009, 7, 12), 11.0, 23.3],
        [datetime(2009, 7, 13), 11.6, 23.7], [datetime(2009, 7, 14), 11.8, 20.7], [datetime(2009, 7, 15), 12.6, 22.4],
        [datetime(2009, 7, 16), 13.6, 19.6], [datetime(2009, 7, 17), 11.4, 22.6], [datetime(2009, 7, 18), 13.2, 25.0],
        [datetime(2009, 7, 19), 14.2, 21.6], [datetime(2009, 7, 20), 13.1, 17.1], [datetime(2009, 7, 21), 12.2, 15.5],
        [datetime(2009, 7, 22), 12.0, 20.8], [datetime(2009, 7, 23), 12.0, 17.1], [datetime(2009, 7, 24), 12.7, 18.3],
        [datetime(2009, 7, 25), 12.4, 19.4], [datetime(2009, 7, 26), 12.6, 19.9], [datetime(2009, 7, 27), 11.9, 20.2],
        [datetime(2009, 7, 28), 11.0, 19.3], [datetime(2009, 7, 29), 10.8, 17.8], [datetime(2009, 7, 30), 11.8, 18.5],
        [datetime(2009, 7, 31), 10.8, 16.1]
    ]

    area_range_plot = AreaRange(
        width='500px',
        height='500px',
        engine='highcharts',
        title='July Temperatures',
        y_axis_title='Temperature',
        y_axis_units='*C',
        series=[{
            'name': 'Temperature',
            'data': averages,
            'zIndex': 1,
            'marker': {
                'lineWidth': 2,
            }
        }, {
            'name': 'Range',
            'data': ranges,
            'type': 'arearange',
            'lineWidth': 0,
            'linkedTo': ':previous',
            'fillOpacity': 0.3,
            'zIndex': 0
        }]
    )

    context = {
        'timeseries_plot': timeseries_plot,
        'multi_timeseries_plot': multi_timeseries_plot,
        'area_range_plot': area_range_plot,
    }

    return render(request, 'hydrologic_modeling/test3.html', context)