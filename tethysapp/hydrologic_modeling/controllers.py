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
from .app_utils import *

try:
    from .app_utils import *
except Exception,e:
    print e



@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    context = {}

    return render(request, 'hydrologic_modeling/home.html', context)



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


def model_run(request):
    """
    Controller that will ........
    """

    # default values
    fac_L_form= ""
    simulation_name = ""
    cell_size = ""
    timestep = ""
    outlet_y = ""
    outlet_x = ""
    box_topY = ""
    box_bottomY =""
    box_rightX = ""
    box_leftX = ""
    simulation_start_date = ""
    simulation_end_date = ""
    timeseries_source = ""
    threshold = ""
    USGS_gage = ""
    observed_hydrograph = ""
    observed_hydrograph_userModified = ""

    user_name = request.user.username

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


    # # ------------ query existing simulation records, and put them on drop down list--------- # #
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

    simulation_names_list = SelectInput(display_text='Saved Models',
                                     name='simulation_names_list',
                                     multiple=False,
                                     options=  queries                #[ (  simulations_queried[0].id, '1'),  (  simulations_queried[1].simulation_name, '2'  ),  (   simulations_queried[1].user_name, '2'  ),
                                     )
    # # ------------ querying ------------- # #

    # NOT WORKING: function to create a ViewPlot timeseries hydrograph
    def create_viewplot_hydrograph(date_in_datetime, Qsim, error):
        # preparing timeseries data in the format shown in: http://docs.tethysplatform.org/en/latest/tethys_sdk/gizmos/plot_view.html#time-series
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

    # to make sure we know which set of inputs we are receiving
    try:
        check_first_request = request.POST['simulation_name']
    except:
        check_first_request = None

    try:
        check_second_request = request.POST['fac_L']
    except:
        check_second_request = None

    current_model_inputs_table_id = 0
    model_inputs_table_id_from_another_html = current_model_inputs_table_id  # :TODO need to check why this works

    if check_first_request != None:
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

        try:
            outlet_shp = request.FILES['outlet_shp']
            watershed_shp = request.FILES['watershed_shp']
        except:
            pass


        # :TODO load all the parameters to the database, and use that information in the block below to retreive

        # :TODO write the inputs in a database

        # use the inputs to create (0r for the time being run) the model

        # :todo some sort of algorith to create a folder name. ini_fname = simulation_name OR may not be required
        temp_folder_name = 'usr1'
        ini_fname= 'BlackSmithFork.ini'

        simulation_folder =  os.path.join(os.path.abspath(os.path.dirname(__file__)) , 'workspaces', 'user_workspaces',temp_folder_name)
        ini_path = os.path.join(simulation_folder, ini_fname )


        # step0
        run_1 = pytopkapi_run_instance(simulation_name=simulation_name, cell_size=cell_size, timestep=timestep,
                                   xy_outlet= [outlet_x,outlet_y ], yyxx_boundingBox=[box_topY, box_bottomY,box_leftX ,box_rightX],
                                   USGS_gage=USGS_gage, list_of_threshold= [threshold] , simulation_folder=simulation_folder)

        # step1_create_ini = run_1.prepare_supporting_ini()           # step1
        # step2_run_model = run_1.run()                             # step2
        date_in_datetime, Qsim, error = run_1.get_Qsim_and_error()



        # # ------------ # #
        # # WE CAN WRITE TO DATABSE BEFORE MODEL IS RUN TOO # #
        # write the inputs to the database
        # :TODO write only when sim_name is different for a user
        # from .model import engine, SessionMaker, Base, model_inputs_table, model_calibration_table
        # # model_calibration_table.__table__.drop(engine)   # to delete the tables, in case anything wrong goes
        # # model_inputs_table.__table__.drop(engine)
        # Base.metadata.create_all(engine)        # Create tables
        # session = SessionMaker()                # Make session
        # one_run = model_inputs_table(user_name, simulation_folder, simulation_name, cell_size, timestep, outlet_y, outlet_x, box_topY,
        #                              box_bottomY, box_rightX, box_leftX, simulation_start_date, simulation_end_date,
        #                              timeseries_source, threshold, USGS_gage)
        # session.add(one_run)
        # session.commit()

        # use function instead to write to db
        inputs_dictionary = {"user_name":user_name, "simulation_name": simulation_name,"simulation_folder": simulation_folder,
                "simulation_start_date": simulation_start_date,"simulation_end_date": simulation_end_date,
                "USGS_gage": USGS_gage,"outlet_x": outlet_x,"outlet_y": outlet_y,
                "box_topY": box_topY,"box_bottomY": box_bottomY,"box_rightX": box_rightX,"box_leftX": box_leftX,
                "timeseries_source": timeseries_source, "threshold":threshold,  "cell_size":cell_size, "timestep":timestep}

        write_to_db_input_as_dictionary(inputs_dictionary, simulation_folder)

        # read the id
        current_model_inputs_table_id = str(len(session.query(model_inputs_table).filter(
                                                    model_inputs_table.user_name == user_name).all()))  # because PK is the same as no of rows, i.e. length
        # # ----------- # #


        # create_viewplot_hydrograph(date_in_datetime, Qsim, error)  # aile kina ho kaam garena

        # preparing timeseries data in the format shown in: http://docs.tethysplatform.org/en/latest/tethys_sdk/gizmos/plot_view.html#time-series
        hydrograph = []
        date_broken = [[dt.year, dt.month, dt.day, dt.hour, dt.minute] for dt in date_in_datetime]
        for i in range(len(Qsim)):
            date = datetime(year=date_broken[i][0], month=date_broken[i][1], day=date_broken[i][2], hour=date_broken[i][3], minute=date_broken[i][4])
            hydrograph.append([ date, float(Qsim[i])   ])

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


    if check_second_request != None :
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


        # # -------DATABASE STUFFS  <start>----- # #
        # retreive the model_inputs_table.id of this entry to pass it to the next page (calibration page)
        from .model import engine, SessionMaker, Base, model_calibration_table
        # Base.metadata.create_all(engine)        # Create tables
        session = SessionMaker()                # Make session

        # STEP1: retrieve the model_inputs_table.id of this entry to pass it to the next page (calibration page)
        current_model_inputs_table_id = str(len(session.query(model_inputs_table).filter(
                                                    model_inputs_table.user_name == user_name).all()))  # because PK is the same as no of rows, i.e. length

        # STEP2: use the id retrieved in STEP1 to get all the remaining parameters
        # :TODO change the sql table to have one field with all the model-parameters seperated by ,say, __
        # instead of many  fields.
        all_rows = session.query(model_inputs_table).filter(model_inputs_table.id == current_model_inputs_table_id).all()
        parameters_retrieved = {}

        for row in all_rows:
            parameters_retrieved['id'] = row.id
            parameters_retrieved['user_name'] = row.user_name
            parameters_retrieved['simulation_folder'] = row.simulation_folder
            parameters_retrieved['simulation_name'] = row.simulation_name
            parameters_retrieved['cell_size'] = row.cell_size
            parameters_retrieved['timestep'] = row.timestep
            parameters_retrieved['outlet_y'] = row.outlet_y
            parameters_retrieved['outlet_x'] = row.outlet_x
            parameters_retrieved['box_topY'] = row.box_topY
            parameters_retrieved['box_bottomY'] = row.box_bottomY
            parameters_retrieved['box_rightX'] = row.box_rightX
            parameters_retrieved['box_leftX'] = row.box_leftX
            parameters_retrieved['simulation_start_date'] = row.simulation_start_date
            parameters_retrieved['simulation_end_date'] = row.simulation_end_date
            parameters_retrieved['timeseries_source'] = row.timeseries_source
            parameters_retrieved['threshold'] = row.threshold
            parameters_retrieved['USGS_gage'] = row.USGS_gage


        # STEP3: create a run instance, which does not run the model but REFERNCES a run instance.
        old_run = pytopkapi_run_instance(simulation_name=parameters_retrieved['simulation_name'],
                                         cell_size=parameters_retrieved['cell_size'],
                                         timestep=parameters_retrieved['timestep'],
                                         xy_outlet= [parameters_retrieved['outlet_x'], parameters_retrieved['outlet_y'] ],
                                         yyxx_boundingBox=[parameters_retrieved['box_topY'], parameters_retrieved['box_bottomY'],parameters_retrieved['box_leftX'] ,parameters_retrieved['box_rightX']],
                                         USGS_gage=parameters_retrieved['USGS_gage'], list_of_threshold= [parameters_retrieved['threshold']] , simulation_folder=parameters_retrieved['simulation_folder'])

        # # STEP4: run model with changed parameters
        # date_in_datetime_UserModified, Qsim_UserModified, error_checking_param_UserModified = old_run.run_model_with_different_parameters(calibration_parameters=[fac_L_form,fac_Ks_form,fac_n_o_form, fac_n_c_form, fac_th_s_form ],
        #                                           numerical_values=[pvs_t0_form, vo_t0_form, qc_t0_form, kc_form ])

        date_in_datetime_UserModified, Qsim_UserModified, error_checking_param_UserModified = old_run.run_model_with_different_parameters(calibration_parameters=[fac_L_form,fac_Ks_form,fac_n_o_form, fac_n_c_form, fac_th_s_form ],
                                                   numerical_values=[pvs_t0_form, vo_t0_form, qc_t0_form, kc_form ])

        # STEP5: get the revised hydrographs, and plot it
        # preparing timeseries data in the format shown in: http://docs.tethysplatform.org/en/latest/tethys_sdk/gizmos/plot_view.html#time-series
        hydrograph2 = []
        date_broken = [[dt.year, dt.month, dt.day, dt.hour, dt.minute] for dt in date_in_datetime_UserModified]
        for i in range(len(Qsim_UserModified)):
            date = datetime(year=date_broken[i][0], month=date_broken[i][1], day=date_broken[i][2], hour=date_broken[i][3],
                            minute=date_broken[i][4])
            hydrograph2.append([date, float(Qsim_UserModified[i])])

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
                'data': hydrograph2
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

    context = {'simulation_name':simulation_name+ str(outlet_y),
               'outlet_y': outlet_y,
               'outlet_x': outlet_x,
               'observed_hydrograph':observed_hydrograph,

               'fac_L': fac_L,
               'fac_Ks': fac_Ks,
               'fac_n_o': fac_n_o,
               "fac_n_c": fac_n_c,
               "fac_th_s": fac_th_s,

               'pvs_t0': pvs_t0,
               'vo_t0': vo_t0,
               'qc_t0': qc_t0,
               "kc": kc,

               'fac_L_form': fac_L_form,
               'user_name':user_name,
               'simulation_names_list':simulation_names_list,
               'Iwillgiveyou_model_inputs_table_id_from_another_html':model_inputs_table_id_from_another_html,
               "model_inputs_table_id":current_model_inputs_table_id,
               "observed_hydrograph_userModified":observed_hydrograph_userModified,
               "test_var": str(get_outlet_xy_from_shp_shx(outlet_shp, simulation_folder)),
               }

    return render(request, 'hydrologic_modeling/model-run.html', context)


def google_map_input(request):

    context = {}
    return render(request, 'hydrologic_modeling/googlemap.html', context)


def model_input(request):

    user_name = request.user.username

    # Define Gizmo Options
    from .model import engine, SessionMaker, Base, model_inputs_table, model_calibration_table
    simulation_names_list = ""          # create_simulation_list_after_querying_db(user_name)

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
    validation_status = True

    if request.is_ajax and request.method == 'POST':
        try:
            validation_status, form_error, inputs_dictionary = validate_inputs(request)

            if form_error.startswith("Error 2") or form_error.startswith("Error 3"):  # may not need this part. Because if no shapefile input, will not read it
                form_error = ""

        except Exception, e:
            if form_error.startswith("Error 2") or form_error.startswith("Error 3"):  # may not need this part. Because if no shapefile input, will not read it
                form_error = ""
            else:
                form_error = "Error 0: " + str(e)

        if not validation_status:
            np.savetxt("/home/prasanna/Documents/a%s.txt"%form_error, np.array([1, 1]))

        if validation_status:

            hydrograph_series = run_model_with_input_as_dictionary(inputs_dictionary, simulation_folder="")




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
    }

    return render(request, 'hydrologic_modeling/model_input.html', context)


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
        'simulation_names_list': create_simulation_list_after_querying_db(user_name),
        'outlet_x': outlet_x, 'outlet_y': outlet_y,
        'north_lat': north_lat, 'east_lon': east_lon, 'west_lon': west_lon, 'south_lat': south_lat,
    }
    return render(request, 'hydrologic_modeling/test2.html', context)


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
