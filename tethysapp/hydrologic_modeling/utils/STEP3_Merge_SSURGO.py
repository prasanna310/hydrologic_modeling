import pandas as pd
import numpy as np
import os

'''

FUTURE IMPROVEMENTS:
1) For the A/B etc. designations in soil group, think about replacing it to a number, may be. or may be AB, AD rather
than replacing them with a single soil group

2) The list 'valuesToAvg' and 'list_fname_ColNo_Headers' could be read from a file
'''

try:
    import arcpy
    path2_ssurgo_or_statsgo = arcpy.GetParameterAsText(0)
    lookupTable = arcpy.GetParameterAsText(1)             # this should be optional
except Exception, e:
    print e

# consider_chorizon_AB = False if all layers need to be considered for weighted averaging
consider_chorizon_AB = True
# calculate SD for layers A, B and H
calculate_sd = True

if path2_ssurgo_or_statsgo == "":
    # Input a folder that has all the folders of names similar to  UT012, Ut027 etc.
    path2_ssurgo_or_statsgo = r"C:\Users\Prasanna\OneDrive\Public\Multiple Watersheds in BRB\STATSGO_folders"
    lookupTable = os.path.join(os.getcwd(), "GREENAMPT_LOOKUPTABLE.csv")    #have not tested though
    # lookupTable = r"C:\Users\Prasanna\Google Drive\RESEARCH\AutoPTPK2\GREENAMPT_LOOKUPTABLE.csv"


def step3_merge_ssurgo(path2_ssurgo_or_statsgo ,path2lookupTable=lookupTable ):
    """
    :param path2_ssurgo_or_statsgo: The path to a folder containing the collection of SSURGO (or Statsgo) folders
    :param path2lookupTable: The greenampt csv lookup table that with soil properties for each soil texture classes
    :return: a csv file in each ssurgo folders, that has soil properties calculated for each map units
    """

    def get_SD(path2_OverallMergedWithTexture_2):
        # a small function, to calculate soil depth for each Map Unit
        merged2 = pd.read_csv(path2_OverallMergedWithTexture_2)

        # VxD = merged['HorizonDepth2'] * merged[valueName];
        # merged.loc[:, valueName + "xD_sum"] = VxD

        chorizonCalc = merged2.groupby('COKEY').agg({'HorizonDepth2': np.sum,
                                                     'ComponentPercent': np.max,
                                                     'COKEY': np.max,
                                                     'MUKEY': np.max})

        chorizonCalc = chorizonCalc.rename(columns={
            'HorizonDepth2': 'SD_sum_component'})  # because grouping by cokey, the column name doesnt match its data

        # percentage weightage
        SD_Perc_X = chorizonCalc['ComponentPercent'].astype('float') / 100. * chorizonCalc['SD_sum_component']
        chorizonCalc.loc[:, 'SD_comp'] = SD_Perc_X

        # now Group it by MUKEY, and done!
        componentPercentageCalc = chorizonCalc.groupby('MUKEY').agg({'MUKEY': np.max, 'SD_comp': np.sum})
        componentPercentageCalc = componentPercentageCalc.rename(columns={'SD_comp': 'SD'})

        # convert cm to m
        componentPercentageCalc['SD'] = componentPercentageCalc['SD'] * .01

        componentPercentageCalc.to_csv(os.path.join(path2tabular, "MUKEY-SD.csv"), index=False)


        # To get Soil Depth for each MU key, sum SD by first grouping/aggregating data in COKEY
        # And then apply weighted average based on Component %

    # # # STEP-I: Read file, list of folders # # #

    # Read the lookup table that maps each soil type to different soil properties. Like Rawls et al (1982)
    lookupTable = pd.read_csv(path2lookupTable , sep=',', skiprows = 0)

    # In the SSURGO/STATSGO folder path given, there will be one or more folders containing SSURGO or STATSGO.
    # Create a list of those folders
    folderList = []
    [folderList.append(folders) for folders in os.listdir(path2_ssurgo_or_statsgo)
        if os.path.isdir(os.path.join(path2_ssurgo_or_statsgo, folders))]

    # # # STEP-II: For each SSURGO/STATSGO folder, create rasters  # # #

    for folder in folderList:

        # # # STEP-III: Initialize # # #
        path2ssurgo= os.path.join(path2_ssurgo_or_statsgo , folder)
        path2tabular = os.path.join(path2ssurgo, "tabular")
        path2Spatial= os.path.join(path2ssurgo, "spatial")

        # The values that we need to average, MAKE CHANGES HERE
        valuesToAvg = ['ksat_r','dbthirdbar_r','dbfifteenbar_r','AWC','Ks', 'ResidualWaterContent', 'Porosity',
                        'EffectivePorosity', 'BubblingPressure_Geometric', 'PoreSizeDistribution_geometric']

        # list_fname_ColNo_Headers [ [filename, [column numbers for fields to pull up], [col headers to be assigned]], ]
        # the number start from 0, so 1 is actually the second column/field
        list_fname_ColNo_Headers = [ ["comp",[1,5,107,108],["ComponentPercent","MajorComponent", "MUKEY","COKEY"]],
                                     ["muaggatt",[10,17,39],["AWC","HydroGrp","MUKEY"]],
                                     ["chorizon",[0,6,9,12,82,72,75,91,94,169,170],["hzname","TopDepth","BottomDepth", "HorizonDepth","ksat_r","dbthirdbar_r","dbfifteenbar_r","wthirdbar_r","wfifteenbar_r","COKEY","CHKEY"]],
                                     ["chtextur",[0,2,3],["textureName","CHtxtgrpKEY","CHTXTKEY"]],
                                     ["chtexgrp",[4,5],["CHKEY","CHtxtgrpKEY"]]
                                     ]

        # # # STEP-IV: Reads necessary SSURGO tables from textfiles, and save as csv with the headers # # #
        def STEP1_rawToRefined( fileName_ColNoList_Headers, path=path2tabular):
            """
            :param fileName_ColNoList_Headers: the list (filename, col numbers, names to the col) = list_fname_ColNo_Headers
            :param path: path2tabular
            :return: file in the memory, as panda dataframe
            """
            for afileColHdr in fileName_ColNoList_Headers:
                txtFilename= afileColHdr[0]
                colNo = afileColHdr[1]
                header = afileColHdr[2]

                txtFile = os.path.join(path, txtFilename + ".txt")   #RETURNS FULL ADDRESS
                csvFileData = pd.read_csv(txtFile, sep = "|",  header=None, comment='#')

                reqdData = csvFileData.iloc[:,colNo]
                reqdData.columns = header
                reqdData.to_csv(os.path.join(path ,  txtFilename + ".csv"), index=False)
            return reqdData

        # # # STEP-V: Merges the muaggatt-component & chtexgrp-chtextur-chorizon. (without LUT values) # # #
        def STEP2_mergeCSV(path=path2tabular):
            muaggatt  = pd.read_csv(path+"/muaggatt.csv") ; print "Total values in muaggatt.csv:", len(muaggatt.index)
            component = pd.read_csv(path+"/comp.csv")    ; print "Total values in comp.csv:", len(component.index)
            chorizon = pd.read_csv(path+"/chorizon.csv")  ; print "Total values in chorizon.csv:", len(chorizon.index)
            chtextur = pd.read_csv(path+"/chtextur.csv")  ; print "Total values in chtextur.csv:", len(chtextur.index)
            chtexgrp = pd.read_csv(path+"/chtexgrp.csv")  ; print "Total values in chtexgrp.csv:", len(chtexgrp.index)

            component_Muaggatt =  pd.merge(muaggatt , component, on='MUKEY')
            chorizon_Component_Muaggatt =  pd.merge(component_Muaggatt , chorizon, on='COKEY')

            chTxt_chTxtGrp =  pd.merge(chtextur , chtexgrp, on='CHtxtgrpKEY')
            merged = pd.merge(chTxt_chTxtGrp , chorizon_Component_Muaggatt, on='CHKEY')

            # print chorizonWithComponent
            merged.to_csv(path + "/MERGED.csv", index=False)
            return merged



        # __main__

        # # # STEP-VI: Merge the 'merged.csv' to LUT on textureName # # #
        try:
            STEP1_rawToRefined(list_fname_ColNo_Headers);
            print "Headers applied to raw txts"
            mergdf = STEP2_mergeCSV();
            print "Merging completed"

            mergeWithLookUp = pd.merge(mergdf, lookupTable, on='textureName')  # >result: OverallMergedWithTexture.csv
            mergeWithLookUp.to_csv(os.path.join(path2tabular, "OverallMergedWithTexture.csv"), index=False)

            print "Merging with texture lookup table completed"

        except Exception, e:
            print e

        # # # STEP-VII: Weighted average Calculations # # #
        try:
            # STEP4 Take i)Height Weighted Average ii)Component % weighted average --------> result MUKEY-Vs-Values.csv
            merged = pd.read_csv(os.path.join(path2tabular, "OverallMergedWithTexture.csv"))

            # Calculation of weighted average
            HorizonDepth2 = merged['BottomDepth'] - merged['TopDepth'] ; merged.loc[:,'HorizonDepth2']= HorizonDepth2

            # CORRECTIONS INCLUDED IN MERGED2: 1)Deleted duplicates Chorizon layers, 2) Layer A & B only considered. H added for statsgo, since they dont do horizon naming
            criterion = merged['hzname'].map(lambda x: x.startswith('A') or x.startswith('B') or x.startswith('H'))
            merged2 = merged[criterion]
            merged2 = merged2.drop_duplicates('CHKEY')
            merged2.to_csv(os.path.join(path2tabular, "OverallMergedWithTexture_2.csv"), index=False) # saving for future

            if consider_chorizon_AB:
                merged = merged2

            # Create the MUKEY VS Soil Depth file
            get_SD(os.path.join(path2tabular, "OverallMergedWithTexture_2.csv"))

            # the values whose weighted average we want, needs to be given in the list below
            # -------> MUKEY Vs Value (just one) MUKEY-Value.csv
            for valueName in valuesToAvg:       # add those values to merged
                VxD = merged['HorizonDepth2']* merged[valueName] ; merged.loc[:,valueName+"xD_sum"]= VxD
                chorizonCalc = merged.groupby('COKEY').agg({valueName+"xD_sum":np.sum ,
                                                            'HorizonDepth2':np.sum,
                                                            'ComponentPercent':np.max,
                                                            'COKEY':np.max,
                                                            'MUKEY':np.max })
                chorizonCalc = chorizonCalc.rename(columns = {'HorizonDepth2':'HorizonDepth2_sum'}) # because grouping by cokey, the column name doesnt match its data

                VxD_by_sum = chorizonCalc[valueName+"xD_sum"].astype('float').div(chorizonCalc['HorizonDepth2_sum'].astype('float'))
                chorizonCalc.loc[:,valueName+"_avgH"]= VxD_by_sum

                # percentage weightage
                compPerc_X_Havg = chorizonCalc['ComponentPercent'].astype('float')/100. * chorizonCalc[valueName+"_avgH"]
                chorizonCalc.loc[:,valueName+"_WtAvg"] = compPerc_X_Havg

                # now Group it by MUKEY, and done!
                componentPercentageCalc = chorizonCalc.groupby('MUKEY').agg({'MUKEY':np.max, valueName+"_WtAvg":np.sum })
                componentPercentageCalc.to_csv(os.path.join(path2tabular, "MUKEY-"+ valueName  +".csv"), index=False)

            # now, function to use the 'valuesToAvg' list above, and merge them against MUKEY
            mukeyValues = componentPercentageCalc.MUKEY



        except Exception, e:
            print e



        try:
            # STEP5: Merge all the MUKEY Vs Values csv --------> result MUKEY-Vs-Values.csv
            lastValueFile = pd.read_csv(path2tabular+"\\MUKEY-"+ valuesToAvg[-1]  +".csv")
            for valueName in valuesToAvg:
                # if valueName == valuesToAvg[-1] : break
                fl = pd.read_csv(path2tabular+"\\MUKEY-"+ valueName  +".csv")
                print path2tabular+"\\MUKEY-"+ valueName  +".csv"
                lastValueFile = pd.merge(lastValueFile, fl, on="MUKEY")

            # add soil depth in here
            if calculate_sd:
                sd_file = pd.read_csv(path2tabular+"\\MUKEY-SD.csv")
                lastValueFile = pd.merge(lastValueFile,sd_file, on="MUKEY")

            # Print mukeyValuesAllMerged
            lastValueFile.to_csv(path2ssurgo+"\\MUKEY-Vs-Values.csv", index=False)
            print 'All values table written down in the ssurgo folder'

            # Create a schema.ini so that arcGIS can understand the MUKEY field
            schema = open(path2ssurgo+"\\schema.ini", "w")
            schema.write("[MUKEY-Vs-Values.csv]"+ "\n" + "Col2=MUKEY Text")  # may not always be column 1 though
            schema.close()

        except Exception, e:
            print e

        try:
            ## adding Soil group to the final table

            final_table =  pd.read_csv(os.path.join(path2_ssurgo_or_statsgo, folder, "MUKEY-Vs-Values.csv"))
            muaggat = pd.read_csv(os.path.join(path2_ssurgo_or_statsgo, folder,"tabular", "muaggatt.csv"))

            # remove duplicate Soil group elements
            # may be replacement is not advisable. Need to double check on this

            muaggat= muaggat.replace("A/B", "B")
            muaggat=muaggat.replace("A/C", "C")
            muaggat=muaggat.replace("B/D", "D")
            muaggat=muaggat.replace("B/C", "C")
            muaggat=muaggat.replace("B/D", "D")
            muaggat=muaggat.replace("C/D", "D")

            muaggat.to_csv(os.path.join(path2_ssurgo_or_statsgo, folder,"tabular", "muaggatt_Removed_HydrGRP.csv"), index=False)

            merge_soilGRP_final = pd.merge(final_table, muaggat, on= 'MUKEY')
            merge_soilGRP_final.to_csv(os.path.join(path2_ssurgo_or_statsgo, folder , "MUKEY-Vs-Values.csv"), index=False)
            print "Merging Soil Hydrologic Group Complete"

            # delete all the csv files made so far, except the MUKEY-Vs-Values.csv
            filelist = [ f for f in os.listdir(path2tabular) if f.endswith(".csv") ]
            for f in filelist:
                # os.remove(os.path.join(path2tabular, f))
                pass

        except Exception,e :
            print "Merging the Hydrologic Soil Group failed with the error %s"%e




if __name__ == "__main__":
    step3_merge_ssurgo( path2_ssurgo_or_statsgo, lookupTable)






