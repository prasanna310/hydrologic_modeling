from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .model import SessionMaker
from tethys_gizmos.gizmo_options import TextInput, DatePicker
from tethys_sdk.gizmos import SelectInput
from tethys_sdk.gizmos import TimeSeries
from datetime import datetime

import sys, os
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
    simulation_names_list = app_utils.create_simulation_list_after_querying_db(user_name)

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



    form_error = ""
    observed_hydrograph = ""
    test_function_response = ""
    table_id = 0
    validation_status = True

    if request.is_ajax and request.method == 'POST':
        try:
            validation_status, form_error, inputs_dictionary = app_utils.validate_inputs(request)

            if form_error.startswith("Error 2") or form_error.startswith("Error 3"):  # may not need this part. Because if no shapefile input, will not read it
                form_error = ""

        except Exception, e:
            if form_error.startswith("Error 2") or form_error.startswith("Error 3"):  # may not need this part. Because if no shapefile input, will not read it
                form_error = ""
            else:
                form_error = "Error 0: " + str(e)

        if not validation_status:
            # useless code. If the file is prepared, we know validatoin status = False
            np.savetxt("/home/prasanna/Documents/a%s.txt"%form_error, np.array([1, 1]))

        if validation_status:
            # hydrograpph series is a series (list) object.
            # table_id is the id of the data just written in the database after the successful model run
            hydrograph_series, table_id = app_utils.run_model_with_input_as_dictionary(inputs_dictionary,False, simulation_folder="")




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



    # # page content, if no request
    # try:
    #     test_function_response = load_shapefile_to_db()
    # except Exception,e:
    #     test_function_response = e


    context = {
        'test_function_response':test_function_response,
        'form_error':form_error,
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
        'outlet_hs': outlet_hs,
        'bounding_box_hs': bounding_box_hs,

        'validation_status':validation_status,
        'form_error':form_error,
        'model_inputs_table_id':table_id

    }

    return render(request, 'hydrologic_modeling/model_input.html', context)


def model_run(request):
    """
    Controller that will display the run result (hydrograph). Also allows user to rerun model based on modifications
    """
    user_name = request.user.username

    fac_L_form= ""
    simulation_name = ""
    outlet_y = ""
    outlet_x = ""

    observed_hydrograph = ""
    observed_hydrograph_userModified = ""
    observed_hydrograph_loaded = ""
    simulation_loaded_id  = ""
    current_model_inputs_table_id = 0
    model_inputs_table_id_from_another_html = 0  # need to make it point to last sim by default

    # :todo some sort of algorith to create a folder name. ini_fname = simulation_name OR may not be required
    temp_folder_name = 'usr1'
    ini_fname = 'BlackSmithFork.ini'
    simulation_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'workspaces', 'user_workspaces',
                                     temp_folder_name)
    ini_path = os.path.join(simulation_folder, ini_fname)


    # gizmo settings
    fac_L = TextInput(display_text='fac_L', name='fac_L', initial=1.0)
    fac_Ks = TextInput(display_text='fac_Ks', name='fac_Ks', initial=1.0)
    fac_n_o = TextInput(display_text='fac_n_o', name='fac_n_o', initial=1.0)
    fac_n_c = TextInput(display_text='fac_n_c', name='fac_n_c', initial=1.0)
    fac_th_s = TextInput(display_text='fac_th_s', name='fac_th_s', initial=1.0)

    pvs_t0 = TextInput(display_text='pvs_t0', name='pvs_t0', initial=90.0)
    vo_t0 = TextInput(display_text='vo_t0', name='vo_t0', initial=100.0)
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
        model_input_load_request = request.POST['simulation_names_list']
        current_model_inputs_table_id = model_input_load_request
        print "MSG: Previous simulation is loaded. The name of simulation loaded is: ", model_input_load_request
    except:
        model_input_load_request = None


    # check to see if the request is from method (3)
    try:
        model_run_calib_request = request.POST['fac_L']
        print 'MSG: Calibration parameters are modified'
    except:
        model_run_calib_request = None

    #model_inputs_table_id_from_another_html = current_model_inputs_table_id  # :TODO need to check why this works

    # Method (1), request from model_input-prepare model
    if model_input_prepare_request != None:
        print 'MSG: Method I initiated.'

        # get input set-1, and create hydrograph
        simulation_name = request.POST['simulation_name']
        cell_size = request.POST['cell_size']
        timestep = request.POST['timestep']

        simulation_start_date = request.POST['simulation_start_date_picker']
        simulation_end_date = request.POST['simulation_end_date_picker']
        timeseries_source = request.POST['timeseries_source']
        threshold = request.POST['threshold']
        USGS_gage = request.POST['USGS_gage']

        outlet_x = request.POST['outlet_x']
        outlet_y = request.POST['outlet_y']
        box_topY = request.POST['box_topY']
        box_bottomY = request.POST['box_bottomY']
        box_rightX = request.POST['box_rightX']
        box_leftX = request.POST['box_leftX']

        model_engine = request.POST['model_engine']

        print "MSG: Inputs from user read"

        try:
            outlet_shp = request.FILES['outlet_shp']
            watershed_shp = request.FILES['watershed_shp']

            print "MSG: Shapefile from user read"
        except:
            pass


        # :TODO load all the parameters to the database, and use that information in the block below to retreive

        # ----------------TODO: Can be replaced with function app_utils.run_model_with_input_as_dictionary function too
        #  write the inputs in a database
        inputs_dictionary = {"user_name":user_name, "simulation_name": simulation_name,"simulation_folder": simulation_folder,
                "simulation_start_date": simulation_start_date,"simulation_end_date": simulation_end_date,
                "USGS_gage": USGS_gage,"outlet_x": outlet_x,"outlet_y": outlet_y,
                "box_topY": box_topY,"box_bottomY": box_bottomY,"box_rightX": box_rightX,"box_leftX": box_leftX,
                "timeseries_source": timeseries_source, "threshold":threshold, "model_engine":model_engine,  "cell_size":cell_size, "timestep":timestep}

        # step0
        run_1 = pytopkapi_run_instance(simulation_name=simulation_name, cell_size=cell_size, timestep=timestep,
                                   xy_outlet= [outlet_x,outlet_y ], yyxx_boundingBox=[box_topY, box_bottomY,box_leftX ,box_rightX],
                                   USGS_gage=USGS_gage, list_of_threshold= [threshold] , simulation_folder=simulation_folder)

        # step1_create_ini = run_1.prepare_supporting_ini()             # step1
        # step2_run_model = run_1.run()                                 # step2
        date_in_datetime, Qsim, error = run_1.get_Qsim_and_error()

        current_model_inputs_table_id = app_utils.write_to_db_input_as_dictionary(inputs_dictionary, simulation_folder)
        print "MSG: Inputs from 'model_input form' written to db. Model RAN. The model_input_id whcih will be used to modify is: ", current_model_inputs_table_id

        # create_viewplot_hydrograph(date_in_datetime, Qsim, error)  # aile kina ho kaam garena

        # preparing timeseries data in the format shown in: http://docs.tethysplatform.org/en/latest/tethys_sdk/gizmos/plot_view.html#time-series
        hydrograph = []
        date_broken = [[dt.year, dt.month, dt.day, dt.hour, dt.minute] for dt in date_in_datetime]
        for i in range(len(Qsim)):
            date = datetime(year=date_broken[i][0], month=date_broken[i][1], day=date_broken[i][2], hour=date_broken[i][3], minute=date_broken[i][4])
            hydrograph.append([ date, float(Qsim[i])   ])
        # ------------------------------------------------------------------------------------------------------------#

        observed_hydrograph = TimeSeries(
        height='500px',
        width='500px',
        engine='highcharts',
        title='Hydrograph ',
        subtitle= "Simulated and Observed flow for "  + simulation_name,
        y_axis_title='Discharge',
        y_axis_units='cumecs',
        series=[{
            'name': 'Simulated Flow',
            'data':hydrograph,
            }]
        )







    # Method (2), request from model_input-load simulation
    if model_input_load_request != None:
        model_run_id = model_input_load_request

        print 'MSG: Method II initiated.'


        # STEP1: Retrieve simulation information from db in a dict
        inputs_dictionary = app_utils.create_model_input_dict_from_db(model_run_id, user_name )

        # # pass the dict to load the result (hydrograph)
        # hydrograph2, table_id = app_utils.run_model_with_input_as_dictionary(inputs_dictionary,False)

        # Because in this part we load previous simulation, we just need to read , not RUN the model


        # STEP2: create a run instance, which does not run the model but REFERNCES a run instance.
        old_run = pytopkapi_run_instance(simulation_name=inputs_dictionary['simulation_name'],
                                         cell_size=inputs_dictionary['cell_size'],
                                         timestep=inputs_dictionary['timestep'],
                                         xy_outlet= [inputs_dictionary['outlet_x'], inputs_dictionary['outlet_y'] ],
                                         yyxx_boundingBox=[inputs_dictionary['box_topY'], inputs_dictionary['box_bottomY'],inputs_dictionary['box_leftX'] ,inputs_dictionary['box_rightX']],
                                         USGS_gage=inputs_dictionary['USGS_gage'], list_of_threshold= [inputs_dictionary['threshold']] , simulation_folder=inputs_dictionary['simulation_folder'])

        # STEP3: Because we are loading the model, not running it,
        date_in_datetime_loaded, Qsim_loaded, error_checking_param_loaded = old_run.get_Qsim_and_error()

        # STEP4: get the dictionary from id, to pass it onto the same html so that we can re-run the rerun! ;)
        current_model_inputs_table_id = app_utils.write_to_db_input_as_dictionary(inputs_dictionary,simulation_folder)
        print "MSG: Inputs from model_input form written to db. Model RAN already"

        # STEP5: get the revised hydrographs, and plot it
        # preparing timeseries data in the format shown in: http://docs.tethysplatform.org/en/latest/tethys_sdk/gizmos/plot_view.html#time-series
        hydrograph2 = []
        date_broken = [[dt.year, dt.month, dt.day, dt.hour, dt.minute] for dt in date_in_datetime_loaded]
        for i in range(len(Qsim_loaded)):
            date = datetime(year=date_broken[i][0], month=date_broken[i][1], day=date_broken[i][2], hour=date_broken[i][3],
                            minute=date_broken[i][4])
            hydrograph2.append([date, float(Qsim_loaded[i])])

        observed_hydrograph_loaded = TimeSeries(
            height='500px',
            width='500px',
            engine='highcharts',
            title=' Corrected Hydrograph ',
            subtitle="Simulated and Observed flow for " + simulation_name,
            y_axis_title='Discharge',
            y_axis_units='cumecs',
            series=[{
                'name': 'Simulated Flow',
                'data': hydrograph2
            }]
        )






    # Method (3), request from model_run, change calibration parameters
    if model_run_calib_request != None :
        # get input set-2, and redraw the hydrographs
        # :TODO Establising connection of inputs from input-set-1 to this block

        fac_L_form = float(request.POST['fac_L'])
        fac_Ks_form = float(request.POST['fac_Ks'])
        fac_n_o_form = float(request.POST['fac_n_o'])
        fac_n_c_form = float(request.POST['fac_n_c'])
        fac_th_s_form = float(request.POST['fac_th_s'])

        pvs_t0_form = float(request.POST['pvs_t0'])
        vo_t0_form = float(request.POST['vo_t0'])
        qc_t0_form = float(request.POST['qc_t0'])
        kc_form = float(request.POST['kc'])

        model_inputs_table_id_from_another_html = request.POST['model_inputs_table_id_from_another_html']
        print 'MSG: Method III initiated. The model id we are looking at is: ', model_inputs_table_id_from_another_html

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


        # following two line should replace the above lines for querring db
        # from .model import model_inputs_table, model_calibration_table

        ## test code, start
        from .model import  SessionMaker, model_inputs_table
        session = SessionMaker()
        for i in range(1, 17):
            all_rows = session.query(model_inputs_table).filter(model_inputs_table.id == i).all()
            print "MSG: TRIAL, printing DB querries"
            for row in all_rows:
                print row.id, row.simulation_name
        ### test code, END

        # create input_dictionary for the last run. Because we are modifying, we need to load the last run
        inputs_dictionary = app_utils.create_model_input_dict_from_db(model_inputs_table_id_from_another_html, user_name )
        print 'MSG: Input Dictionary from db of model_input_id= ', model_inputs_table_id_from_another_html, " created for simulation: ", inputs_dictionary['simulation_name']

        # STEP3: create a run instance, which does not run the model but REFERNCES a run instance.
        old_run = pytopkapi_run_instance(simulation_name=inputs_dictionary['simulation_name'],
                                         cell_size=inputs_dictionary['cell_size'],
                                         timestep=inputs_dictionary['timestep'],
                                         xy_outlet= [inputs_dictionary['outlet_x'], inputs_dictionary['outlet_y'] ],
                                         yyxx_boundingBox=[inputs_dictionary['box_topY'], inputs_dictionary['box_bottomY'],inputs_dictionary['box_leftX'] ,inputs_dictionary['box_rightX']],
                                         USGS_gage=inputs_dictionary['USGS_gage'], list_of_threshold= [inputs_dictionary['threshold']] , simulation_folder=inputs_dictionary['simulation_folder'])

        # # # STEP4: run model with changed parameters
        # date_in_datetime_UserModified, Qsim_UserModified, error_checking_param_UserModified = old_run.run_model_with_different_parameters(calibration_parameters=[fac_L_form,fac_Ks_form,fac_n_o_form, fac_n_c_form, fac_th_s_form ],
        #                                            numerical_values=[pvs_t0_form, vo_t0_form, qc_t0_form, kc_form ])

        # Step 4 placeholder, JUST READS. SO :TODO Del this step4 and retain above step4
        date_in_datetime_UserModified, Qsim_UserModified, error_checking_param_UserModified = old_run.get_Qsim_and_error()

        # write to DB, as a fresh simulation.So this helps in identifying this simulation next time user wants to modify
        # because we are re-writing previous simulations in this step, we use same evth (hence, simulation_folder)a s b4
        current_model_inputs_table_id = app_utils.write_to_db_input_as_dictionary(inputs_dictionary, inputs_dictionary['simulation_folder'])


        # STEP5: get the revised hydrographs, and plot it
        # preparing timeseries data in the format shown in: http://docs.tethysplatform.org/en/latest/tethys_sdk/gizmos/plot_view.html#time-series
        hydrograph3 = []
        date_broken = [[dt.year, dt.month, dt.day, dt.hour, dt.minute] for dt in date_in_datetime_UserModified]
        for i in range(len(Qsim_UserModified)):
            date = datetime(year=date_broken[i][0], month=date_broken[i][1], day=date_broken[i][2], hour=date_broken[i][3],
                            minute=date_broken[i][4])
            hydrograph3.append([date, float(Qsim_UserModified[i])])

        observed_hydrograph_userModified = TimeSeries(
            height='500px',
            width='500px',
            engine='highcharts',
            title=' Corrected Hydrograph ',
            subtitle="Simulated and Observed flow for " + simulation_name,
            y_axis_title='Discharge',
            y_axis_units='cumecs',
            series=[{
                'name': 'Simulated Flow',
                'data': hydrograph3
            }]
        )

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
               'observed_hydrograph':observed_hydrograph,

               'fac_L': fac_L, 'fac_Ks': fac_Ks, 'fac_n_o': fac_n_o, "fac_n_c": fac_n_c, "fac_th_s": fac_th_s,
               'pvs_t0': pvs_t0,  'vo_t0': vo_t0, 'qc_t0': qc_t0,   "kc": kc,

               'fac_L_form': fac_L_form,
               'user_name':user_name,

               #'Iwillgiveyou_model_inputs_table_id_from_another_html':model_inputs_table_id_from_another_html,
               "current_model_inputs_table_id":current_model_inputs_table_id, # model_inputs_table_id

               "observed_hydrograph_userModified":observed_hydrograph_userModified,
               "observed_hydrograph_loaded":observed_hydrograph_loaded,
               #"simulation_loaded_id":simulation_loaded_id,

               }

    return render(request, 'hydrologic_modeling/model-run.html', context)


def google_map_input(request):

    context = {}
    return render(request, 'hydrologic_modeling/googlemap.html', context)



def test2(request):
    user_name = request.user.username

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
    outlet_x = TextInput(display_text='Longitude', name='outlet_x', initial='-111.7915')
    outlet_y = TextInput(display_text='Latitude', name='outlet_y', initial=' 41.74025')

    north_lat = TextInput(display_text='North Y', name='north_lat', initial='41.7215')
    east_lon = TextInput(display_text='East X', name='east_lon', initial='-111.8461 ')
    west_lon = TextInput(display_text='West X', name='west_lon', initial='-111.6208')
    south_lat = TextInput(display_text='South Y', name='south_lat', initial='41.88')





    context = {
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
        'simulation_names_list': app_utils.create_simulation_list_after_querying_db(user_name),
        'outlet_x': outlet_x, 'outlet_y': outlet_y,
        'north_lat': north_lat, 'east_lon': east_lon, 'west_lon': west_lon, 'south_lat': south_lat,
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
