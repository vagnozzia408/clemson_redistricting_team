# -*- coding: utf-8 -*-
"""
Created on Thu Oct 14 16:15:58 2021

@author: aburt
"""

import arcpy,math,os,sys
#import networkx as nx
#import numpy as np
        
def arcprint(message,*variables):
    '''Prints a message using arcpy.AddMessage() unless it can't; then it uses print. '''
    if runspot == "ArcGIS":
        arcpy.AddMessage(message.format(*variables))
    elif runspot == "console":
        newmessage=message
        j=0
        while j<len(variables): #This while loop puts the variable(s) in the correct spot(s) in the string
            newmessage = newmessage.replace("{"+str(j)+"}",str(variables[j])) #Replaces {i} with the ith variable
            j=j+1
        print(newmessage)
    else: 
        raise RuntimeError("No value for runspot has been assigned")

def arcerror(message,*variables):
    '''Prints an error message using arcpy.AddError() unless it can't; then it uses print. '''
    if runspot == "ArcGIS":
        arcpy.AddError(message.format(*variables))
    elif runspot == "console":
        newmessage=message
        j=0
        while j<len(variables): #This while loop puts the variable(s) in the correct spot(s) in the string
            newmessage = newmessage.replace("{"+str(j)+"}",str(variables[j])) #Replaces {i} with the ith variable
            j=j+1
        raise RuntimeError(newmessage)
    else: 
        raise RuntimeError("No value for runspot has been assigned")

#%% START MAIN CODE
def main(*args):
    global runspot #Allows runspot to be changed inside a function
    
    if sys.executable == r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe": #Change this line if ArcGIS is located elsewhere
        runspot = "ArcGIS"
    else:
        runspot = "console"
            
    # Set environment settings
    global currentdir
    global path
    global in_table
    
    currentdir = os.getcwd()
    path = currentdir + "\\precincts_2020_copy.gdb"
    #path = currentdir
    arcpy.env.workspace = path
    
    arcpy.env.overwriteOutput = True
    
    try: #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
        in_table = sys.argv[1]
        in_name_field = sys.argv[2]
        
    except IndexError: 
        try: #Second, tries to take input from explicit input into main()
            in_table = args[0]
            in_name_field = args[1]
           
        except IndexError: #Finally, manually assigns input values if they aren't provided
#            in_table=path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1"
#            in_pop_field = "SUM_Popula"
#            in_name_field = "OBJECTID"
            in_table = path + "\\Statewide_2020_cleaning"
            in_name_field = "OBJECTID_1"
            
    # There are 3 main types of map errors: Overlapping precincts, Gaps in between precincts, and Discontiguous precincts. 
    ## First we deal with Overlapping precincts. 2 overlapping precincts create an intersection,
    ## we identify all of these intersections using the arcpy function PairwiseIntersect. 
    intersect_out_table = in_table + "_Intersections"
    arcpy.analysis.PairwiseIntersect(in_table, intersect_out_table, "ALL", None, "INPUT")
    
    # The plan was to use Clip (Modify Features) to remove these overlaps, however currently I have not been able to find an ArcPy 
    # implentation of this tool, only one for Clip (Analysis) which works very differently. 
    
    
    aprx = arcpy.mp.ArcGISProject(currentdir + "\\precincts_2020_copy.aprx")
    aprxMap = aprx.listMaps("Map")[0] 
    layername = intersect_out_table.replace(path+'\\','')
    layer = aprxMap.listLayers(layername)
    if not layer: #if the layer currently does not exist in the table of contents:
        aprxMap.addDataFromPath(intersect_out_table)
    aprx.save()
    
    ## Now we must work on gaps in between precincts
    
    
    
    
    
#END FUNCTIONS    
if __name__ == "__main__":
    main()
                