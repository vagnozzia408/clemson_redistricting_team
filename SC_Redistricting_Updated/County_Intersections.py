# -*- coding: utf-8 -*-
"""
Created on Mon Sep  6 12:12:47 2021

@author: blake
"""

import arcpy,math,os,sys
import numpy as np
import random


def CountIntersections(dist1, dist2, cur_count, Matrix, in_table, in_dist_field, cur_square):
    hyp_count = cur_count - np.count_nonzero(Matrix[dist1-1]) - np.count_nonzero(Matrix[dist2-1])
    hyp_square = cur_square - np.sum(np.square(Matrix[dist1-1])) - np.sum(np.square(Matrix[dist2-1]))
    Temp_Matrix = np.zeros([2,46], dtype=int)
    with arcpy.da.SearchCursor(in_table, [in_dist_field,'County'], '''{}={} OR {}={}'''.format(in_dist_field,dist1,in_dist_field,dist2)) as cursor:
        for row in cursor:
            if row[0]==dist1:
                Temp_Matrix[0][int((int(row[1])-1)/2)] +=1
            if row[0]==dist2:
                Temp_Matrix[1][int((int(row[1])-1)/2)] +=1
    hyp_count += np.count_nonzero(Temp_Matrix[0]) + np.count_nonzero(Temp_Matrix[1])
    hyp_square += np.sum(np.square(Temp_Matrix[0])) + np.sum(np.square(Temp_Matrix[1]))
    return(hyp_count, Temp_Matrix,hyp_square) 

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
        arcprint("We are running this from inside ArcGIS")
    else:
        runspot = "console"
        arcprint("We are running this from the python console")   
            
    # Set environment settings
    global currentdir
    global path
    
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
            in_table = path + "\\Precincts_2020"
            distcount = 7
            in_dist_field = "Dist_Assgn"
            arcprint("We are using default input choices")
    
    with arcpy.da.UpdateCursor(in_table, in_dist_field) as cursor:
        for row in cursor:
            row[0] = random.randint(0,7)
            cursor.updateRow(row)
    
    #CDI = County-District-Intersection
    global units_in_CDI
    units_in_CDI = np.zeros([distcount,46], dtype=int)
    
    with arcpy.da.SearchCursor(in_table, [in_dist_field,'County']) as cursor:
        for row in cursor:
            units_in_CDI[int(row[0])-1][int((int(row[1])-1)/2)] +=1
    
    CDI_Count = np.count_nonzero(units_in_CDI)
    arcprint("CDI_Count = {0}",CDI_Count)
    
    #Squares each entry of the matrix and adds them all together
    CDI_Square = np.sum(np.square(units_in_CDI))
    
    return(units_in_CDI,CDI_Count,CDI_Square)
    
#END FUNCTIONS    
if __name__ == "__main__":
    main()