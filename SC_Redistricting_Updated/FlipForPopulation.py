# -*- coding: utf-8 -*-
"""
Created on Thu Nov  4 14:03:05 2021

@author: blake & amy
"""
import arcpy,os,sys
import numpy as np

#%% START MAIN CODE
def main(*args):
    global runspot #Allows runspot to be changed inside a function
    
    if sys.executable == r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe": #Change this line if ArcGIS is located elsewhere
        runspot = "ArcGIS"
        arcprint("We are running this from inside ArcGIS")
    else:
        runspot = "console"
        arcprint("We are running this from the python console")   
            
    # Set environment settings
    
    currentdir = os.getcwd()
    path = currentdir + "\\SC_Redistricting_Updated.gdb"
    arcpy.env.workspace = path
    
    try: #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
        in_table = sys.argv[1]
        distcount = sys.argv[2]
        in_dist_field = sys.argv[3]
    except IndexError: 
        try: #Second, tries to take input from explicit input into main()
            in_table = args[0]
            distcount = args[1]
            in_dist_field = args[2]
        except IndexError: #Finally, manually assigns input values if they aren't provided
            in_table = path + "\\Precincts_2020_SA_7dists_701507575_100it"
            distcount = 7
            in_dist_field = "Dist_Assgn"
            arcprint("We are using default input choices")
    
 
    
    return()
    
#END FUNCTIONS    
if __name__ == "__main__":
    main()
