import os
import numpy as np
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)) ,"../", 'PyTOPKAPI'))


try:
    import pytopkapi
except Exception, e:
    print e

try:
    from .. import PyTOPKAPI
except Exception, e:
    print e


import ConfigParser
from ConfigParser import SafeConfigParser
import shutil

def create_config_files_create_file(simulation_folder, tiff_folder,pVs_t0=90., Vo_t0=1000., Qc_t0=0, Kc=1.0 ):
    if not os.path.exists(simulation_folder):
        os.makedirs(simulation_folder)

    configWrite = ConfigParser.RawConfigParser()
    configWrite.add_section('raster_files')
    configWrite.set('raster_files', 'dem_fname', tiff_folder+"/DEM_Prj_fc.tif")
    configWrite.set('raster_files', 'mask_fname', tiff_folder+  "/mask_r.tif" )
    configWrite.set('raster_files', 'soil_depth_fname', tiff_folder + "/SD-sc.tif")
    configWrite.set('raster_files', 'conductivity_fname', tiff_folder + "/ksat-tc.tif")
    configWrite.set('raster_files', 'hillslope_fname',tiff_folder+ "/slope_c.tif")
    configWrite.set('raster_files', 'sat_moisture_content_fname', tiff_folder+ '/por-tc.tif')
    configWrite.set('raster_files', 'resid_moisture_content_fname', tiff_folder+ '/rsm-tc.tif' )
    configWrite.set('raster_files', 'bubbling_pressure_fname',tiff_folder+ '/bbl-tc.tif')
    configWrite.set('raster_files', 'pore_size_dist_fname', tiff_folder+ '/psd-tc.tif' )
    configWrite.set('raster_files', 'overland_manning_fname', tiff_folder+ '/n_Overland.tif' )
    configWrite.set('raster_files', 'channel_network_fname', tiff_folder+ '/str_cr255.tif')
    configWrite.set('raster_files', 'flowdir_fname', tiff_folder+ '/fdr_cr.tif' )
    configWrite.set('raster_files', 'channel_manning_fname', tiff_folder+ '/n_Channel.tif' )
    configWrite.set('raster_files', 'flowdir_source',  'ArcGIS' )


    configWrite.add_section('output')
    configWrite.set('output', 'param_fname', simulation_folder+"/cell_param_unmodified.dat")

    configWrite.add_section('numerical_values')
    configWrite.set('numerical_values', 'pVs_t0', pVs_t0)
    configWrite.set('numerical_values','Vo_t0', Vo_t0 )
    configWrite.set('numerical_values','Qc_t0',Qc_t0 )
    configWrite.set('numerical_values','Kc', Kc)

    with open(os.path.join(simulation_folder,'create_file.ini'), 'wb') as configFile:
        configWrite.write(configFile)

    return

def create_config_files_zero_slope_mngmt(simulation_folder, cell_size=30.92208078 ):
    if not os.path.exists(simulation_folder):
        os.makedirs(simulation_folder)

    configWrite = ConfigParser.RawConfigParser()
    configWrite.add_section('input_files')
    configWrite.set('input_files', 'file_cell_param', simulation_folder+'/cell_param_unmodified.dat')

    configWrite.add_section('output_files')
    configWrite.set('output_files', 'file_cell_param_out',simulation_folder+'/cell_param.dat')


    configWrite.add_section('numerical_values')
    configWrite.set('numerical_values', 'nb_param', 21)
    configWrite.set('numerical_values', 'X', cell_size)

    with open(os.path.join(simulation_folder,'zero_slope_management.ini'), 'wb') as configFile:
        configWrite.write(configFile)

    return

def create_config_files_plot_flow_precip(simulation_folder,path_to_runoff_file, outlet_ID ,calibration_start_data='01/01/2015' ):
    if not os.path.exists(simulation_folder+"/results"):
        os.makedirs(simulation_folder+"/results")

    configWrite = ConfigParser.RawConfigParser()
    configWrite.add_section('files')
    configWrite.set('files', 'file_Qsim', simulation_folder+'/results/results.h5')
    configWrite.set('files', 'file_Qobs',  path_to_runoff_file)
    configWrite.set('files', 'file_rain', simulation_folder+'/rainfields.h5')
    configWrite.set('files', 'image_out', simulation_folder+'/results')

    configWrite.add_section('groups')
    configWrite.set('groups', 'group_name','sample_event')


    configWrite.add_section('parameters')
    configWrite.set('parameters', 'outlet_ID', outlet_ID)
    configWrite.set('parameters', 'graph_format', 'png')
    configWrite.set('parameters', 'start_calibration', calibration_start_data  +" ;dd/mm/yyyy")

    configWrite.add_section('flags')
    configWrite.set('flags', 'Qobs', 'True')
    configWrite.set('flags', 'Pobs', 'True')
    configWrite.set('flags', 'nash', 'True')
    configWrite.set('flags', 'R2', 'True')
    configWrite.set('flags', 'RMSE', 'True')
    configWrite.set('flags', 'RMSE_norm', 'True')
    configWrite.set('flags', 'Diff_cumul', 'True')
    configWrite.set('flags', 'Bias_cumul', 'True')
    configWrite.set('flags', 'Err_cumul', 'True')
    configWrite.set('flags', 'Abs_cumul', 'True')


    with open(os.path.join(simulation_folder,'plot-flow-precip.ini'), 'wb') as configFile:
        configWrite.write(configFile)

    return

def create_config_files_plot_soil_moisture_map(simulation_folder,t1=1, t2=5, variable=4, fac_L=1., fac_Ks=1., fac_n_o=1., fac_n_c=1. ):
    if not os.path.exists(simulation_folder+"/SM"):
        os.makedirs(simulation_folder+"/SM")

    configWrite = ConfigParser.RawConfigParser()
    configWrite.add_section('files')
    configWrite.set('files', 'file_global_param', simulation_folder+'/global_param.dat')
    configWrite.set('files', 'file_cell_param', simulation_folder+'/cell_param.dat')
    configWrite.set('files', 'file_sim', simulation_folder+'/results/results.h5')

    configWrite.add_section('paths')
    configWrite.set('paths', 'path_out', simulation_folder +"/SM")


    configWrite.add_section('calib_params')
    configWrite.set('calib_params', 'fac_L', fac_L)
    configWrite.set('calib_params', 'fac_Ks', fac_Ks)
    configWrite.set('calib_params', 'fac_n_o', fac_n_o)
    configWrite.set('calib_params', 'fac_n_c', fac_n_c)

    configWrite.add_section('flags')
    configWrite.set('flags', 't1', t1)
    configWrite.set('flags', 't2', t2)
    configWrite.set('flags', 'variable', variable)

    with open(os.path.join(simulation_folder,'plot-soil-moisture-maps.ini'), 'wb') as configFile:
        configWrite.write(configFile)

    return

def create_config_files_TOPKAPI_ini(simulation_folder, external_flow_status= 'False', append_output_binary = 'False',fac_L = 1.4, fac_Ks = 1. ,fac_n_o  = 1. ,fac_n_c  = 1., fac_th_s = 1 ):

    if not os.path.exists(simulation_folder):
        os.makedirs(simulation_folder)

    configWrite = ConfigParser.RawConfigParser()

    configWrite.add_section('input_files')
    configWrite.set('input_files', 'file_global_param', simulation_folder+"/global_param.dat")
    configWrite.set('input_files', 'file_cell_param', simulation_folder+ "/cell_param.dat" )
    configWrite.set('input_files', 'file_rain', simulation_folder + "/rainfields.h5")
    configWrite.set('input_files', 'file_ET', simulation_folder + "/ET.h5")

    configWrite.add_section('output_files')
    configWrite.set('output_files', 'file_out', simulation_folder+"/results/results.h5")
    configWrite.set('output_files', 'file_change_log_out', simulation_folder+  "/results/change_result_log.dat" )
    configWrite.set('output_files', 'append_output', append_output_binary )

    configWrite.add_section('groups')
    configWrite.set('groups', 'group_name', 'sample_event')

    configWrite.add_section('external_flow')
    configWrite.set('external_flow', 'external_flow', 'False')
    if external_flow_status.lower() == 'true':
        print "External flow parameters need to be entered here"

    configWrite.add_section('numerical_options')
    configWrite.set('numerical_options', 'solve_s', 1)
    configWrite.set('numerical_options','solve_o',1 )
    configWrite.set('numerical_options','solve_c',1 )
    configWrite.set('numerical_options','only_channel_output', 'False')

    configWrite.add_section('calib_params')
    configWrite.set('calib_params', 'fac_L', fac_L)
    configWrite.set('calib_params', 'fac_Ks', fac_Ks)
    configWrite.set('calib_params', 'fac_n_o', fac_n_o)
    configWrite.set('calib_params', 'fac_n_c', fac_n_c)
    configWrite.set('calib_params', 'fac_th_s', fac_th_s)


    with open(os.path.join(simulation_folder,'TOPKAPI.ini'), 'wb') as configFile:
        configWrite.write(configFile)

    return

def create_cell_param( create_file_ini_file, zero_slope_mngmt_ini_file):

    import sys
    sys.path.append('../../PyTOPKAPI')

    from pytopkapi.parameter_utils.create_file import generate_param_file
    from pytopkapi.parameter_utils import modify_file

    # Generate Parameter Files
    generate_param_file(create_file_ini_file, isolated_cells=False)
    print "Cell Parameter file created"

    # slope corrections
    modify_file.zero_slope_management(zero_slope_mngmt_ini_file)
    print "Zero Slope corrections made"

    return

def create_global_param(simulation_folder, A_thres=25, X=30.92208078, Dt=86400, W_min=1., W_Max=10.):
    title = ['X', 'Dt', 'Alpha_s', 'Alpha_o', 'Alpha_c', 'A_thres', 'W_min', 'W_max']
    values = [X, Dt, 2.5,1.6666667, 1.6666667, A_thres*1000000., W_min , W_Max]
    values = [str(item) for item in values]
    with open(simulation_folder+"/global_param.dat", "wb") as g_param_file:
        string = "\t\t".join(title)+ '\n' + "\t\t".join(values)
        g_param_file.write(string)
        #g_param_file.write(values)

def create_rain_ET_file(simulation_folder, total_no_of_cell, ppt_file_txt ):
    import h5py, numpy

    # output path
    rainfall_outputFile = os.path.join(simulation_folder, "rainfields.h5")
    ET_outputFile = os.path.join(simulation_folder, "ET.h5")


    # 1_del (for removing file readings)
    rain_from_file = numpy.genfromtxt(ppt_file_txt, delimiter='\t')

    time_step = rain_from_file.shape[0]
    no_of_cell = total_no_of_cell # 3400
    # rainfall_intensity_perUnitTime = 20 #mm
    rainfall_reduction_factor = 1

    with h5py.File(rainfall_outputFile,'w') as f2:

        f2.create_group('sample_event')
        f2['sample_event'].create_dataset('rainfall', shape=(time_step, no_of_cell), dtype='f' )

        rainArray =  f2['sample_event']['rainfall']
        data = numpy.zeros((time_step , no_of_cell))
        for i in range(time_step):
            # 2_del (for removing file readings)
            rainfall_intensity_perUnitTime = rain_from_file[i][-1] * rainfall_reduction_factor
            a = numpy.empty( (1,no_of_cell ) )
            a.fill(rainfall_intensity_perUnitTime)  #
            data[i,:] = a

        # data[0,:] = numpy.zeros((1,no_of_cell))
        # data[time_step/4,:] = numpy.zeros((1,no_of_cell))
        # data[time_step/2,:] = numpy.zeros((1,no_of_cell))
        # data[time_step/3,:] = numpy.zeros((1,no_of_cell))
        rainArray[:] = data



    with h5py.File(ET_outputFile,'w' ) as f1:
        f1.create_group('sample_event')
        f1['sample_event'].create_dataset('ETo', shape=( time_step, no_of_cell), dtype='f' )
        f1['sample_event'].create_dataset('ETr', shape=( time_step, no_of_cell), dtype='f' )

        EToArray =  f1['sample_event']['ETo']
        ETrArray =  f1['sample_event']['ETr']

        data = numpy.zeros((time_step , no_of_cell))
        for i in range(time_step):
            data[i,:] = numpy.random.rand(1,no_of_cell)*0.0

        EToArray = data
        ETrArray = data



def get_outletID_noOfCell(cell_para_file):
    cell_param_array = np.genfromtxt(cell_para_file, delimiter=' ')
    no_of_cell = cell_param_array.shape[0]

    # outlet_ID is the first element (cell lable) of parameter for the cell whose d/s id = -999
    outlet_ID = cell_param_array[cell_param_array[:,14] < -99][0][0]
    return int(outlet_ID), no_of_cell

def get_cellSize(tif_file):
    try:
        from osgeo import gdal
        dset = gdal.Open( tif_file)

        x0, dx, fy, y0, fx, dy = dset.GetGeoTransform()
    except Exception,e:
        dx = ""
        print ("Either no GDAL, or no tiff file")
    return  dx

def check_hdf5(hdf5_filename):
    import h5py
    import matplotlib.pyplot as plt

    with  h5py.File(hdf5_filename , "r") as f:

        print "The groups in the h5 files are: "
        for group in f.keys():
            print "\t\t" , group,
        # print items / tables inside the group

        for group in f.keys():
            print "\n the Items in the group %s are:"%group
            try:
                for table in f[group]:
                    # if table == 'Qc_out':
                    print "\t\t" , table

                    print 'The size of the hdf5 table is ', f[group][table].shape
                    print 'And, the unique values in the tables are: \n'
                    print np.unique(f[group][table])

                    values_in_1D = f[group][table][:].reshape(-1)
                    plt.hist(values_in_1D,bins=20)
                    plt.show()
            except:
                pass

def get_hydrograph( simulation_folder,  file_Qobs, outlet_ID):
    '''
    Parameters
    ----------
    image_out: fname for image of hydrographs
    file_Qobs: path to text file containing conserved value series
    outlet_ID: outlet_ID

    Returns
    -------
    list1 -> list, error checking parameters such as nash, rsme etc.
    list2 -> list, Q_simulated
    '''
    import pytopkapi
    import pytopkapi.utils as ut
    from pytopkapi.results_analysis import plot_Qsim_Qobs_Rain as pt

    from datetime import datetime

    file_Qsim= simulation_folder + "/results/results.h5"
    group_name= 'sample_event'
    Qobs= True
    Pobs= False
    nash= True



    #Read the obs
    #Qobs
    ar_date, ar_Qobs = pt.read_observed_flow(file_Qobs)


    #Read the simulated data Q
    file_h5=file_Qsim
    ndar_Qc_out=ut.read_one_array_hdf(file_h5,'Channel','Qc_out')
    ar_Qsim=ndar_Qc_out[1:,outlet_ID]

    # error estimation
    nash_value = ut.Nash(ar_Qsim,ar_Qobs)
    RMSE= ut.RMSE(ar_Qsim,ar_Qobs)
    RMSE_norm = ut.RMSE_norm(ar_Qsim,ar_Qobs)
    Bias_cumul= ut.Bias_cumul(ar_Qsim,ar_Qobs)
    Diff_cumul= ut.Diff_cumul(ar_Qsim,ar_Qobs)
    Abs_cumul = ut.Abs_cumul(ar_Qsim,ar_Qobs)
    Err_cumul = ut.Err_cumul(ar_Qsim,ar_Qobs)



   # added to include all in the label

    # if  hydrograph_fname == '':
    #     image_out = simulation_folder+'/results/calibration/Result_'+ str(datetime.now()).replace(':','-')[:-7] + '.png'
    # # create path_out if it does'nt exist
    # ut.check_file_exist(image_out)
    # # #Rain
    # if Pobs:
    #     h5file = h5py.File(file_rain)
    #
    #     dset_string = '/%s/rainfall' % group_name
    #     ndar_rain = h5file[dset_string][...]
    #
    #     h5file.close()
    #     #Compute the mean catchment rainfall
    #     ar_rain=np.average(ndar_rain,axis=1)

    # ##Graph
    # import matplotlib.pyplot as plt
    # from matplotlib.dates import date2num
    # delta = date2num(ar_date[1]) - date2num(ar_date[0])
    #
    # tab_col=['k','r']
    # tab_style=['-','-']
    # tab_width=['1','1']
    # color_P='b'
    # transparency_P=0.5#(0 for invisible)
    #
    # RMSE = ut.RMSE(ar_Qsim, ar_Qobs) ;lines += ax.plot(ar_date[0:1], ar_Qsim[0:1], 'w:') ; tab_leg.append(('RMSE = '+str(RMSE)[0:5]))
    # RMSE_norm = ut.RMSE_norm(ar_Qsim, ar_Qobs)   ;lines += ax.plot(ar_date[0:1], ar_Qsim[0:1], 'w:') ;  tab_leg.append(('RMSE_norm = '+str(RMSE_norm)[0:5]))
    # Bias_cumul = ut.Bias_cumul(ar_Qsim, ar_Qobs) ; lines += ax.plot(ar_date[0:1], ar_Qsim[0:1], 'w:') ; tab_leg.append(('Bias_cumul = '+str(Bias_cumul)[0:5]))
    # Diff_cumul = ut.Diff_cumul(ar_Qsim, ar_Qobs) ; lines += ax.plot(ar_date[0:1], ar_Qsim[0:1], 'w:'); tab_leg.append(('Diff_cumul = '+str(Diff_cumul)[0:5]))
    # Abs_cumul = ut.Abs_cumul(ar_Qsim, ar_Qobs)   ; lines += ax.plot(ar_date[0:1], ar_Qsim[0:1], 'w:'); tab_leg.append(('Abs_cumul = '+str(Abs_cumul)[0:5]))
    # Err_cumul = ut.Err_cumul(ar_Qsim, ar_Qobs)   ; lines += ax.plot(ar_date[0:1], ar_Qsim[0:1], 'w:'); tab_leg.append(('Err_cumul = '+str(Err_cumul)[0:5]))
    # image_out = simulation_folder +'/results/calibration/'+ hydrograph_fname+".png"
    # fig, ax = plt.subplots()
    #
    # lines = []
    # tab_leg = []
    # if Qobs:
    #     lines += ax.plot(ar_date, ar_Qobs,
    #                      color=tab_col[-1],
    #                      linestyle=tab_style[-1], linewidth=tab_width[-1])
    #     tab_leg.append(('Observation'))
    #     tab_leg = tab_leg[::-1] # extended slicing. This Reverses the order
    #
    # lines += ax.plot(ar_date, ar_Qsim,
    #                  color=tab_col[0],
    #                  linestyle=tab_style[0], linewidth=tab_width[0])
    # tab_leg.append('Model')
    # lines += ax.plot(ar_date[0:1], ar_Qsim[0:1], 'w:')
    # tab_leg.append(('Eff = '+str(nash_value)[0:5]))
    #
    # ax.set_xlim(ar_date[0], ar_date[-1])
    # ytitle=r'$Q \  (m^3/s)$'
    # ax.set_ylabel(ytitle, fontsize=18)
    # ax.set_title("Calib:Param_"+hydrograph_fname)
    #
    # ax2 = ax.twinx()
    #
    # # ax2.set_ylabel(r'$Rainfall \ (mm)$', fontsize=18, color=color_P)
    # # ax2.bar(ar_date, ar_rain, width=delta,
    # #         facecolor='blue', edgecolor='blue', alpha=transparency_P)
    # # ax2.set_ylim(max(ar_rain)*2, min(ar_rain))
    #
    # ax2.legend(lines, tab_leg, loc='upper right', fancybox=True)
    # leg = ax2.get_legend()
    # leg.get_frame().set_alpha(0.75)
    #
    # for label in leg.get_texts():
    #     label.set_fontsize('8')
    #
    # # rotate and align the tick labels so they look better,
    # # unfortunately autofmt_xdate doesn't work with twinx due to a bug
    # # in matplotlib <= 1.0.0 so we do it manually
    # ## fig.autofmt_xdate()
    #
    # bottom=0.2
    # rotation=30
    # ha='right'
    #
    # for ax in fig.get_axes():
    #     if hasattr(ax, 'is_last_row') and ax.is_last_row():
    #         for label in ax.get_xticklabels():
    #             label.set_ha(ha)
    #             label.set_rotation(rotation)
    #     else:
    #         for label in ax.get_xticklabels():
    #             label.set_visible(False)
    #         ax.set_xlabel('')
    #
    # fig.subplots_adjust(bottom=bottom)
    #
    # fig.savefig(image_out)
    # #plt.show()



    error_checking_param = [str(nash_value)[0:5], str(RMSE)[0:5],str(RMSE_norm)[0:5],str(Bias_cumul)[0:5],str(Diff_cumul)[0:5],str(Abs_cumul)[0:5],str(Err_cumul)[0:5]]

    return ar_date ,ar_Qsim, error_checking_param

def download_daily_discharge(USGS_siteCode, beginDate, endDate,outFile, Q_max_min_mean= "mean"):
    # Example of calling GetValuesObject from a WaterOneFlow web service
    # Then create a time series plot using matplotlib
    from suds.client import Client
    from pandas import Series
    import matplotlib.pyplot as plt

    # Create the inputs needed for the web service call
    wsdlURL = 'http://hydroportal.cuahsi.org/nwisuv/cuahsi_1_1.asmx?WSDL'
    NWIS = Client(wsdlURL).service

    variableCode = 'NWISUV:00060'

    siteCode = 'NWISUV:' + USGS_siteCode
    beginDate = beginDate #'2015-08-01'
    endDate = endDate #'2015-11-06'

    # Create a new object named "NWIS" for calling the web service methods


    # Call the GetValuesObject method to return datavalues
    response = NWIS.GetValuesObject(siteCode, variableCode, beginDate, endDate)

    # Get the site's name from the response
    try:
        siteName = response.timeSeries[0].sourceInfo.siteName
    except Exception, e:
        print 'ERROR: SiteCode: %s does not have the data'%USGS_siteCode
        return

        # Create some blank lists in which to put the values and their dates
    a = []  # The values
    b = []  # The dates

    # Get the values and their dates from the web service response
    values = response.timeSeries[0].values[0].value

    # Loop through the values and load into the blank lists using append
    for v in values:
        a.append(float(v.value))
        b.append(v._dateTime)

    # Create a Pandas Series object from the lists
    # Set the index of the Series object to the dates
    ts = Series(a, index=b)

    # resample is like group by clause in SQL
    # summed = ts.resample('1D', how='sum')                            #ts.resample('1440T', how='sum')
    ts_maxx = ts.resample('1D').max
    ts_minn = ts.resample('1D').min
    ts_mean = ts.resample('1D').mean

    # try:
    #     # Use MatPlotLib to create a plot of the time series
    #     # Create a plot of the streamflow statistics
    #     # ------------------------------------------
    #     # Create a figure object and add a subplot
    #     # figure() creates  a big area where we can create multiple or single drawings
    #     fig = plt.figure()
    #     ax = fig.add_subplot(1, 1, 1)  # arguments for add_subplot - add_subplot(nrows, ncols, plot_number)
    #
    #     # Call the plot() methods on the series object to plot the data
    #     ts.plot(color='0.9', linestyle='solid', label='15-minute streamflow values')
    #     ts_maxx.plot(color='red', linestyle='solid', label='Daily streamflow values', marker="o")
    #     ts_mean.plot(color='green', linestyle='solid', label='Daily streamflow values', marker="o")
    #     ts_minn.plot(color='blue', linestyle='solid', label='Daily streamflow values', marker="o")
    #
    #     # Set some properties of the subplot to make it look nice
    #     ax.set_ylabel('Discharge, cubic feet per second')
    #     ax.set_xlabel('Date')
    #     ax.grid(True)
    #     ax.set_title(siteName)
    #
    #     # Add a legend with some customizations
    #     legend = ax.legend(loc='upper left', shadow=True)
    #
    #     # Create a frame around the legend.
    #     frame = legend.get_frame()
    #     frame.set_facecolor('0.95')
    #
    #     # Set the font size in the legend
    #     for label in legend.get_texts():
    #         label.set_fontsize('large')
    #
    #     for label in legend.get_lines():
    #         label.set_linewidth(1.5)  # the legend line width
    #
    #
    #     # # plt.show()
    #
    #     plt.savefig('../../data/discharge/' + USGS_siteCode + ".png")
    # except Exception, e:
    #     print "FAILURE: Matplotlib graph preparation"

    r = ts_mean
    print r
    r.to_csv(outFile)

    # change format of the date in the saved file
    # replace - with ,
    f = file(outFile, "r")
    str_to_save = f.read().replace('-',",")
    f.close()

    #save it again
    f = file(outFile, "w")
    f.write(str_to_save)

    f = np.loadtxt(outFile, delimiter=",")
    q = f[:,-1]
    q = q * 0.028316847

    # to make shape of q (x,1) instead of (x,)
    qq = np.zeros((q.shape[0], 1))
    qq[:, 0] = q


    # take the first 3 columns,
    # add two extra colum = 0 0 for min and sec
    # add third column = q
    # save by seperating by space " "
    date_part = f[:,:-1]
    empty_col = np.zeros((f.shape[0],1))
    date_n_hour = np.append(date_part,empty_col, axis =1 )
    date_hour_n_min = np.append(date_n_hour, empty_col, axis=1)
    date_hr_min_n_Q = np.append(date_hour_n_min,qq, axis=1)
    np.savetxt(outFile,date_hr_min_n_Q, fmt='%i %i %i %i %i %f' , delimiter= "\t")

    return

def download_and_resample_discharge_data(USGS_Gage, begin_date='2015-01-01', end_date='2015-12-31',out_fname='Q_cfs', resampling_time = '1D', resampling_method='mean'):
    """
    Downloads, and then resamples the discharge data from USGS using the url of the format:
    http://nwis.waterdata.usgs.gov/usa/nwis/uv/?cb_00060=on&format=rdb&site_no=10109000&period=&begin_date=2015-10-01&end_date=2015-10-31
    INPUT:
    USGS_Gage :     string, e.g. 10109000
    begin_date=     string, e.g. '2015-01-01'
    end_date=       string, e.g. '2015-12-31'
    out_fname=      string, e.g. 'Q_cfs'
    resampling_time=  string, e.g. '1D'
    resampling_method=string, e.g.'mean'
    """

    import urllib2
    import pandas as pd

    urlString3 = 'http://nwis.waterdata.usgs.gov/usa/nwis/uv/?cb_00060=on&format=rdb&site_no=%s&period=&begin_date=%s&end_date=%s'%(USGS_Gage, begin_date, end_date)

    response = urllib2.urlopen(urlString3)  # instance of the file from the URL
    html = response.read()                  # reads the texts into the variable html

    with open('Q_raw.txt', 'w') as f:
        f.write(html)

    df = pd.read_csv('Q_raw.txt', delimiter='\t' , skiprows=26, names=['agency_cd', 'USGS_Station_no', 'datatime', 'timezone', 'Q_cfs','Quality'])

    # convert datetime from string to datetime
    df.iloc[:, 2] = pd.to_datetime(df.iloc[:, 2])

    # create a different dataframe with just the values and datetime
    df_datetime_val = df[['datatime', 'Q_cfs']]

    # convert the values to series
    values = []
    dates = []

    # add values to the list a
    for v in df_datetime_val.iloc[:,1]:
        values.append(float(v))

    # add datatime to list b
    for v in df_datetime_val.iloc[:, 0]:
        dates.append(v)

    # prepare a panda series
    ts = pd.Series(values, index=dates)

    # resample to daily or whatever
    # ts_mean = ts.resample('1D', how='mean') #or
    # ts_mean = ts.resample('1D').mean()
    ts_mean = ts.resample(resampling_time, how=resampling_method)


    # save
    ts_mean.to_csv(out_fname)


def run_model_with_different_parameters(run_name, simulation_folder,  outlet_ID, runoff_file, calibration_parameters,initial_numerical_values= ""):
    """
    Parameters
    ----------
    calibration_parameters: a list, of calibration parameters. [fac_L, fac_Ks, fac_n_o, fac_n_c, fac_th_s]
    initial_numerical_values: a list, of initial numeric values [pvs_t0,vo_t0,qc_t0, kc  ]
    simulation_folder: folder where results and everything are there

    Returns: a list. [Runname, date_time, nash value,\t, [Q_sim]]
    -------
    """
    import pytopkapi

    fac_L = calibration_parameters[0]
    fac_Ks = calibration_parameters[1]
    fac_n_o = calibration_parameters[2]
    fac_n_c = calibration_parameters[3]
    fac_th_s = calibration_parameters[4]

    create_config_files_TOPKAPI_ini(simulation_folder, 'False', 'False', fac_L, fac_Ks, fac_n_o, fac_n_c, fac_th_s)

    # make changes to numerical value section in cell_param.dat
    if initial_numerical_values != "":
        cell_param_array = np.genfromtxt(simulation_folder + '/cell_param.dat', delimiter=' ')

        pvs_t0 = initial_numerical_values[0] # located at col-16 (15 in index)
        vo_t0 = initial_numerical_values[1]  # located at col-17 (16 in index)
        qc_t0 = initial_numerical_values[2]  # located at col-18 (17 in index)
        kc = initial_numerical_values[3]     # located at col-19 (18 in index)

        # change the values that exist
        cell_param_array[:, 15] = np.zeros((int(cell_param_array[:, 15].shape[0]),)) + pvs_t0
        cell_param_array[:, 16] = np.zeros((int(cell_param_array[:, 16].shape[0]),)) + vo_t0
        cell_param_array[:, 17] = np.zeros((int(cell_param_array[:, 17].shape[0]),)) + qc_t0
        cell_param_array[:, 18] = np.zeros((int(cell_param_array[:, 18].shape[0]),)) + kc

        np.savetxt(simulation_folder + '/cell_param.dat',cell_param_array , delimiter=' ')


    # run the program now
    pytopkapi.run(simulation_folder+'/TOPKAPI.ini')

    ar_date, ar_Qsim, error_checking_param = get_hydrograph( simulation_folder, runoff_file, outlet_ID)

    return ar_date ,ar_Qsim, error_checking_param


def preprocess_input_tiffs(ini_fname=''):
    import arcpy
    from STEP1_Get_DEM_LANDUSE import step1_get_dem_landuse
    from STEP2_DEM_Processing import step2_dem_processing
    from STEP4_Join_Merge_Export import STEP4_Join_Merge_Export

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
    if ini_fname != "":

        # initializing
        config = SafeConfigParser()
        config.read(ini_fname)

        # read from initializing file
        # Flags or Binary
        download_data = config.getboolean('preprocessing_flags', 'download_data')
        process_dem = config.getboolean('preprocessing_flags', 'process_dem')
        extract_ssurgo_data = config.getboolean('preprocessing_flags', 'extract_ssurgo_data')
        merge_ssurgo_to_raster = config.getboolean('preprocessing_flags', 'merge_ssurgo_to_raster')

        del_downloaded_files = config.getboolean('preprocessing_flags', 'del_downloaded_files')
        del_ssurgo_files = config.getboolean('preprocessing_flags', 'del_ssurgo_files')
        del_demProcessed_files = config.getboolean('preprocessing_flags', 'del_demProcessed_files')

        # Path to the Input shape files
        outlet_fullpath = config.get('preprocessing_input_files', 'outlet_fullpath')
        wshedBoundary = config.get('preprocessing_input_files', 'wshedBoundary')

        # Input Variables
        inUsername = config.get('preprocessing_input_variables', 'inUsername')
        inPassword = config.get('preprocessing_input_variables', 'inPassword')
        areaThreshold = config.get('preprocessing_input_variables', 'areaThreshold')
        bufferDi = config.get('preprocessing_input_variables', 'bufferDi')
        cell_size = config.get('preprocessing_input_variables', 'cell_size')
        outCS = config.get('preprocessing_input_variables', 'outCS')

        # workspaces
        projDir = config.get('preprocessing_workspaces', 'projDir')
        path2ssurgoFolders = config.get('preprocessing_workspaces', 'ssurgo_collection')
        path2statsgoFolders = config.get('preprocessing_workspaces', 'statsgo_collection')

        tiff_folder = config.get('preprocessing_workspaces', 'out_tiff_folder')


    # list of empty directories to be made
    folders_to_create = [ 'DEM_processes','SSURGO_rasters', 'TIFFS']

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
        if not os.path.exists(raw_files_outDir):
            arcpy.CreateFileGDB_management(projDir, "Raw_files.gdb")
        if not os.path.exists(downloads_outDir):
            arcpy.CreateFileGDB_management(projDir, "Downloads.gdb")

    except Exception, e:
        arcpy.AddMessage(e)

    arcpy.env.workspace = arcpy.env.scratchWorkspace = projDir

    if download_data:
        # Step1, download the data
        step1_get_dem_landuse(inUsername,inPassword,downloads_outDir ,wshedBoundary,bufferDi, outCS)

    if process_dem:
        # Step2
        DEM_fullpath = os.path.join(downloads_outDir, "DEM_Prj")
        land_use_fullpath = os.path.join(downloads_outDir, "Land_Use_Prj")

        if not download_data:
            DEM_fullpath = downloads_outDir+"/DEM"
            land_use_fullpath = os.path.join(downloads_outDir, "Land_Use")

        step2_dem_processing(DEM_fullpath, land_use_fullpath ,raw_files_outDir , outlet_fullpath, areaThreshold,cell_size, outCS)

    if extract_ssurgo_data:
        # Step3
        try:
            from STEP3_Merge_SSURGO import step3_merge_ssurgo
            lookupTable = os.path.join(os.getcwd(), "GREENAMPT_LOOKUPTABLE.csv")
            step3_merge_ssurgo(path2ssurgoFolders ,path2lookupTable=lookupTable )
            step3_merge_ssurgo(path2statsgoFolders ,path2lookupTable=lookupTable )
        except Exception,e:
            arcpy.AddMessage(e)

    if merge_ssurgo_to_raster:
        # Step4
        MatchRaster = os.path.join(raw_files_outDir, "mask_r")
        STEP4_Join_Merge_Export (path2ssurgoFolders, path2statsgoFolders, ssurgo_outDir, MatchRaster )

    # To tif, and flt
    for outRaster in ["mask_r", "DEM_Prj_fc",  "n_Overland", "n_Channel", "fdr_cr" , "slope_c", "SD", "str_c", "str_cr9999", "str_cr255"]:
        arcpy.RasterToOtherFormat_conversion(Input_Rasters="'%s'"%(os.path.join(raw_files_outDir, outRaster)), Output_Workspace=tiffs_outDir, Raster_Format="TIFF")

    for outRaster in ["bbl-tc.tif", "efpo-tc.tif", "ksat-tc.tif",  "psd-tc.tif", "por-tc.tif", "rsm-tc.tif", "SD-sc.tif", "AWC-sc.tif" ]:
        arcpy.RasterToOtherFormat_conversion(Input_Rasters="'%s'"%(os.path.join(ssurgo_outDir, outRaster)), Output_Workspace=tiffs_outDir, Raster_Format="TIFF")

    # delete unnecessary files
    # unnecessary files in TIF folder, that are not tif
    for file in os.listdir(tiffs_outDir):
        if not file.split(".")[-1] in ['tif', "gdb", "xlsx"] :
            os.remove(os.path.join(tiffs_outDir,file))
    try:
        for file in os.listdir(ssurgo_outDir):
            if file.split(".")[-1] in ['tif' , 'TEMP']:
                os.remove(os.path.join(ssurgo_outDir,file))
    except Exception,e:
        print "FAILED: Temporary files deletion"

    # copy files
    try:
        # tif_folder = folder where tiff are supposed to be saved for pytopkapi
        # tif_outDir = folder where tiff are created by the script above
        if not os.path.exists(tiff_folder):
            os.mkdir(tiff_folder)
        for file in os.listdir(tiffs_outDir):
            shutil.copyfile(os.path.join(tiffs_outDir,file), os.path.join(tiff_folder,file) )

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
    return "SUCCESS: Input Raster files creation"

def run_pyTOPKAPI(ini_fname):
    return "Work in Progress"

    # Calibration #


    ## MAIN PROGRAM ##

    preprocess_input_tiffs(ini_fname)



    # get cell size, input a tiff, if not given as input

    cell_size = get_cellSize(in_tiff_folder + '/mask_r.tif')

    # create ini : create_file.ini
    create_config_files_create_file(simulation_folder,in_tiff_folder,pVs_t0=pVs_t0, Vo_t0=Vo_t0)

    # create ini : zero_slope_management.ini
    create_config_files_zero_slope_mngmt(simulation_folder, cell_size)

    # create global parameter files
    # todo: automate Dt, and try W_min and W_max
    create_global_param(simulation_folder, A_thres=areaThreshold, X=cell_size, Dt=86400, W_min=5., W_Max=30.)

    # create the parameter file
    # using the built in create_file script
    # Also executes the zero slope corrections
    create_cell_param(simulation_folder+'/create_file.ini', simulation_folder+'/zero_slope_management.ini')

    # run_simulation
        # create forcing files

    outlet_ID, no_of_cell = get_outletID_noOfCell(simulation_folder+'/cell_param.dat')
    if create_forcing_files:

        # create hdf5 rainfall and ET files
        # get total number of cells, and the
        # todo: ET is right now all zero. Change this.
        create_rain_ET_file(simulation_folder, no_of_cell, ppt_file_txt=precipitation_file)


        create_config_files_TOPKAPI_ini(simulation_folder, append_output_binary='False', fac_L=1.,
                                        fac_Ks=1., fac_n_o=1., fac_n_c=1., fac_th_s=1)

        # create ini: plot-flow-precip.ini
        create_config_files_plot_flow_precip(simulation_folder,Q_observed_file,outlet_ID)

        # create ini: plot-soil-moisture-map.ini
        create_config_files_plot_soil_moisture_map(simulation_folder)

    # RUN THE MODEL
    pytopkapi.run(simulation_folder + '/TOPKAPI.ini')



    if calibrate_the_model:
        simulation_folder = config.get('simulation_forcing_files', 'simulation_folder')
        Q_observed_file = config.get('simulation_results', 'Q_observed_file')

        if not os.path.exists(simulation_folder+'/results'):
            os.mkdir(simulation_folder+'/results')

        if not os.path.exists(simulation_folder + '/results/calibration'):
            os.mkdir(simulation_folder + '/results/calibration')

        # # create a blank file
        # open(simulation_folder + "/results/calibration/run_log.txt", 'a').close()

        # add headers to it, sort of metadata
        with open(simulation_folder + "/results/calibration/run_log.txt", 'a') as f:
            f.write('Calib param: fac_L|fac_Ks|fac_n_o|fac_n_c|fac_th_s '
                    '\t Numeric Param:  pvs_t0|vo_t0|qc_t0|kc '
                    '\t Errors: nash_value|RMSE|RMSE_norm|Bias_cumul|Diff_cumul|Abs_cumul|Err_cumul\n')

        # get the outlet_ID
        config = SafeConfigParser()
        config.read(simulation_folder+'/plot-flow-precip.ini')

        # outlet_ID
        outlet_id = config.getint('parameters', 'outlet_id')

        calib_factor_range = [x/100. for x in range(10,300,50)]

        i = 1

        # following 4 lines are for NUMERICAL PARAMETER
        for pvs_t0 in  [ 30., 95.]:
            for vo_t0 in [100.,2000.]:
                for qc_t0 in [0. ]:
                    for kc in [1]:

                        # following 5 lines are for CALIBRATION PARAMETER
                        for fac_L in  [0.1, 1., 4. ]:
                            for fac_Ks in [1., 4.]:
                               for fac_n_o in  [1.]:
                                    for fac_n_c in [1.]:
                                        for fac_th_s in [1]:

                                            calib_param = [fac_L,fac_Ks,fac_n_o,fac_n_c,fac_th_s ]
                                            numeric_param = [pvs_t0,vo_t0,qc_t0, kc ]

                                            run_name = str(i)+"_" + "-".join(str(item) for item in calib_param) + "-".join(str(item) for item in numeric_param)

                                            # get the error parameters (nash_value, RMSE, RMSE_norm, Bias_cumul, Diff_cumul, Abs_cumul, Err_cumul)
                                            # and the simulated discharge for each timestep
                                            # the model run using this function takes calibration parameter and numeric parameter as input

                                            error_checking_param, Q_sim = run_model_with_different_parameters(run_name,simulation_folder, outlet_id, Q_observed_file, calib_param,numeric_param)

                                            with open(simulation_folder+'/results/calibration/run_log.txt', "a+") as run_log:
                                                run_log.write('\n'+run_name + '\t'
                                                              + "|".join(str(item) for item in calib_param)+  '\t'
                                                              +"|".join(str(item) for item in numeric_param)+  '\t'
                                                              +"|".join(str(item) for item in error_checking_param)
                                                              + '\tQ_sim: '
                                                              + " ".join(str(item) for item in Q_sim))

                                            i = i +1

    def simulate(create_forcing_files= False):
        simulation_folder = config.get('simulation_forcing_files', 'simulation_folder')


        # Simulations Results
        draw_hydrograph = config.getboolean('simulation_results', 'draw_hydrograph')
        draw_maps = config.getboolean('simulation_results', 'draw_maps')
        Q_observed_file = config.get('simulation_results', 'Q_observed_file')
        variable_id_for_maps = config.getfloat('simulation_results', 'variable_id_for_maps')

        outlet_ID, no_of_cell = get_outletID_noOfCell(simulation_folder+'/cell_param.dat')
        if create_forcing_files:

            # create hdf5 rainfall and ET files
            # get total number of cells, and the
            # todo: ET is right now all zero. Change this.
            create_rain_ET_file(simulation_folder, no_of_cell, ppt_file_txt=precipitation_file)

            create_config_files_TOPKAPI_ini(simulation_folder, append_output_binary='False', fac_L=1.,
                                            fac_Ks=1., fac_n_o=1., fac_n_c=1., fac_th_s=1)

            # create ini: plot-flow-precip.ini
            create_config_files_plot_flow_precip(simulation_folder,Q_observed_file,outlet_ID)

            # create ini: plot-soil-moisture-map.ini
            create_config_files_plot_soil_moisture_map(simulation_folder)

        # RUN THE MODEL
        pytopkapi.run(simulation_folder + '/TOPKAPI.ini')

        observed_hydrograph = 'work in progress'
        return observed_hydrograph

    #simulate()
    return simulation_folder

def trial():
	return "This works ,and the paths is %s" %os.path.join(os.path.abspath(os.path.dirname(__file__)) , 'PyTOPKAPI')


class pytopkapi_run_instance:
    import pytopkapi

    def __init__(self, simulation_name, cell_size, timestep, xy_outlet, yyxx_boundingBox, USGS_gage,
                 list_of_threshold, simulation_folder):

        self.name = simulation_name
        self.simulation_folder = simulation_folder
        self.in_tiff_folder = os.path.join(self.simulation_folder, 'TIFFS')
        self.cell_size = cell_size
        self.timestep = timestep

        self.x_outlet = xy_outlet[0]
        self.y_outlet = xy_outlet[1]
        self.y_top = yyxx_boundingBox[0]
        self.y_btm = yyxx_boundingBox[1]
        self.x_lft = yyxx_boundingBox[2]
        self.x_rt = yyxx_boundingBox[3]

        self.threshold = list_of_threshold
        self.USGS_gage = USGS_gage

        # default numeric parameters
        self.pVs_t0 = 90.0
        self.Vo_t0 = 100.0
        self.qc_t0 = 0.0
        self.kc = 1.0

        # default calibration parameters
        self.fac_L = 1.0
        self.fac_Ks = 1.0
        self.fac_n_o = 1.0
        self.fac_n_c = 1.0
        self.fac_th_s = 1.0

        self.path_precipitation_file = os.path.join(self.simulation_folder, 'Rainfall.txt')
        self.path_ET_file = os.path.join(self.simulation_folder, 'ET.txt')

        self.Q_observed_file = os.path.join(self.simulation_folder, 'Runoff.dat')

        return

    # :todo TPREPARING TIFF FILES. But for the first part of project, already created files will be used
    def prepare_tiffs(self):
        # download DEM, NLCD
        # path to LUT, defaulted
        # soil querries etc.
        pass

    # :todo PREPARING FORCING FILES.
    def prepare_forcing_files(self, timeseries_source,start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.timeseries_source = timeseries_source

        # if certain source, do something. Else do other things

        #
        pass

    def prepare_supporting_ini(self):

        # global_parameter.dat
        cell_size = get_cellSize(os.path.join(self.simulation_folder, "TIFFS", "mask_r.tif"))

        if cell_size == "":
            cell_size = self.cell_size  # if gdal or tiff file is absence, the line below returns nothing. so

        create_global_param(self.simulation_folder,A_thres=float(self.threshold[0]),X=float(cell_size),Dt=float(self.timestep)*3600)

        # zero_slope_management.ini
        create_config_files_zero_slope_mngmt(simulation_folder=self.simulation_folder)

        # TOPKAPI.ini
        create_config_files_TOPKAPI_ini(simulation_folder=self.simulation_folder)

        a = os.path.join(self.simulation_folder, "TIFFS")
        # return a

        # create_file.ini
        create_config_files_create_file(simulation_folder=self.simulation_folder,tiff_folder=os.path.join(self.simulation_folder,"TIFFS"),
                                        pVs_t0=self.pVs_t0, Vo_t0=self.Vo_t0, Qc_t0=self.qc_t0, Kc=self.kc)



        return a


    def run(self,  calibration_parameters="", numerical_values=""):
        """
        Parameters
        ----------
        calibration_parameters: a list, of calibration parameters. [fac_L, fac_Ks, fac_n_o, fac_n_c, fac_th_s]
        initial_numerical_values: a list, of initial numeric values [pvs_t0,vo_t0,qc_t0, kc  ]
        simulation_folder: folder where results and everything are there

        Returns: a list. [Runname, date_time, nash value,\t, [Q_sim]]
        -------
        """


        self.numerical_values = numerical_values

        # these values are already there in the init, so not necessary to input them to run the model
        if calibration_parameters != "":
            self.fac_L = calibration_parameters[0]
            self.fac_Ks = calibration_parameters[1]
            self.fac_n_o = calibration_parameters[2]
            self.fac_n_c = calibration_parameters[3]
            self.fac_th_s = calibration_parameters[4]

        create_config_files_TOPKAPI_ini(self.simulation_folder, 'False', 'False', self.fac_L, self.fac_Ks,
                                        self.fac_n_o, self.fac_n_c, self.fac_th_s)

        # make changes to numerical value section in cell_param.dat
        if numerical_values != "":
            self.cell_param_array = np.genfromtxt(self.simulation_folder + '/cell_param.dat', delimiter=' ')

            self.pvs_t0 = numerical_values[0] # located at col-16 (15 in index)
            self.vo_t0 = numerical_values[1]  # located at col-17 (16 in index)
            self.qc_t0 = numerical_values[2]  # located at col-18 (17 in index)
            self.kc = numerical_values[3]     # located at col-19 (18 in index)

            # change the values that exist
            self.cell_param_array[:, 15] = np.zeros((int(self.cell_param_array[:, 15].shape[0]),)) + self.pvs_t0
            self.cell_param_array[:, 16] = np.zeros((int(self.cell_param_array[:, 16].shape[0]),)) + self.vo_t0
            self.cell_param_array[:, 17] = np.zeros((int(self.cell_param_array[:, 17].shape[0]),)) + self.qc_t0
            self.cell_param_array[:, 18] = np.zeros((int(self.cell_param_array[:, 18].shape[0]),)) + self.kc

            np.savetxt(self.simulation_folder + '/cell_param.dat', self.cell_param_array, delimiter=' ')


        self.outlet_ID, self.no_of_cell = get_outletID_noOfCell(self.simulation_folder+'/cell_param.dat')

        # run the program now
        pytopkapi.run(self.simulation_folder + '/TOPKAPI.ini')

        return "successfully ran the simulation"
    def get_Qsim_and_error(self):
        print "At pytopkapi_utils, 1165: get_Qsim_and_error"

        self.outlet_ID, self.no_of_cell = get_outletID_noOfCell(self.simulation_folder + '/cell_param.dat')
        self.date, self.ar_Q_sim, self.error_checking_param= get_hydrograph(self.simulation_folder,
                                                                  self.Q_observed_file, self.outlet_ID)

        print "Date and Q-simulated array read from the prepared run"
        return self.date, self.ar_Q_sim, self.error_checking_param

    def get_cell_size_demo(self):

        cell_size = get_cellSize(self.in_tiff_folder + '/mask_r.tif')
        outlet_ID, no_of_cell = get_outletID_noOfCell(self.simulation_folder + '/cell_param.dat')
        return str(outlet_ID)+"--"+str(cell_size)

    def run_model_with_different_parameters(self,  calibration_parameters,  numerical_values=""):
        outlet_ID, no_of_cell = get_outletID_noOfCell(self.simulation_folder + '/cell_param.dat')

        ar_date, ar_Qsim, error_checking_param =  run_model_with_different_parameters(self.name, self.simulation_folder, outlet_ID,  self.Q_observed_file,
                                            calibration_parameters,  numerical_values)
        
        return  ar_date ,ar_Qsim, error_checking_param

if __name__ == '__main__':
    # initialize_fname, initializing file for TIF (input files) creation, not for running the model
    collection_of_wshed = [ 'EastCanyonCreek', 'EastForkLittleBear',
                            'HobbleCreek', 'LostCreek' , 'SouthForkOgdenRiver','StrawberryRiver'  ]
    # for wshed_to_simulate in collection_of_wshed:
    #     run_pyTOPKAPI('../../../Multiple Watersheds in BRB/%s/%s.ini' % (wshed_to_simulate, wshed_to_simulate))
    #     # try:
    #     #     print ('../../../Multiple Watersheds in BRB/%s/%s.ini' % (wshed_to_simulate, wshed_to_simulate))
    #     # except Exception, e:
    #     #     print 'Unsuccessful for ', wshed_to_simulate

    # download_daily_discharge('10105900', '2015-01-01', '2015-12-30', '../../../Multiple Watersheds in BRB/LittleBearRiver/Runoff_2015.dat', Q_max_min_mean="mean")
    # download_and_resample_discharge_data('10109000', begin_date='2015-01-01', end_date='2015-12-31')

    # outlet_ID = get_outletID_noOfCell('../../../Multiple Watersheds in BRB/LoganRiver/cell_param.dat')
    # plot_sim_observed('../../../Multiple Watersheds in BRB/LoganRiver/', '../../../Multiple Watersheds in BRB/LoganRiver/Runoff.dat', 5354)


    # create_rain_ET_file('../../../Multiple Watersheds in BRB/LoganRiver/',outlet_ID,
    #                     '../../../Multiple Watersheds in BRB/LoganRiver/Rainfall.txt')
    #
    run_1 = pytopkapi_run_instance(simulation_name="pr", cell_size=300, timestep=6,
                                   xy_outlet=[80, 90], yyxx_boundingBox=[50, 60, 50, 85],
                                   USGS_gage=1000, list_of_threshold=[100],
                                   simulation_folder='/usr/lib/tethys/src/tethys_apps/tethysapp/my_first_app/workspaces/user_workspaces/usr1')

    # run_1.run()
    date_in_datetime, Qsim, error = run_1.get_Qsim_and_error()
    print type(Qsim)
    print Qsim
    # Qsim_list = [list(item) for item in Qsim]

    ar_date, ar_Qsim, error_checking_param = run_1.run_model_with_different_parameters(
        calibration_parameters=[1.1, 1.2, 1.2, 1.5, 1.8],
        numerical_values=[90., 100., 1., 1.])




    # pytopkapi.run('../workspaces/user_workspaces/usr1/TOPKAPI.ini')



