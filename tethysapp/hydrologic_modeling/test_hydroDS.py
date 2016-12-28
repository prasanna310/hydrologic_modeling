import sys, os
from hs_restclient import HydroShare
import urlparse

path = os.path.dirname(os.path.realpath(__file__)) + "/hydrogate_python_client"
sys.path.append(path)

from hydrogate import HydroDS
HDS = HydroDS(username="pdahal", password="pDahal2016")

# HDS.uploadfile(r'/usr/lib/tethys/src/tethys_apps/tethysapp/my_first_app/workspaces/user_workspaces/usr1/TIFFS/mask_r.tif')
# HDS.upload_package('/usr/lib/tethys/src/tethys_apps/tethysapp/my_first_app/workspaces/user_workspaces/usr1/TIFFS/mask_r.tif')

DEM = '/home/prasanna/Downloads/Avalanche/DEM_Prj_f.tif'
uploaded_DEM = HDS.upload_file(file_to_upload=DEM)



print "The file name is %s, and the directory saved at is %s" %(DEM, uploaded_DEM )




# # uploaded_file_url = "http://hydro-ds.uwrl.usu.edu/files/data/user_8/mask_r_y0obuQz.tif"   , an example
# split = urlparse.urlsplit(uploaded_DEM)    # type is SplitResult :(
# split2 = (split[:])                             # type is tuple
# full_path_again = urlparse.urlunsplit(split2)





# full code, that can handle error
# try:
#     response_data = HDS.upload_file(file_to_upload=my_file_to_upload)
#     uploaded_file_url = response_data
#
#     # print the url path for the uploaded file
#     print(uploaded_file_url)
# except Exception as ex:
#     print(ex.message)

