# -*- coding: utf-8 -*-
"""
Created on Mon Sep  6 12:12:47 2021

@author: Blake Splitter and Amy Burton
"""

import arcpy,os,sys
import numpy as np
import random
seed = 1738


def CountIntersections(dist1, dist2, cur_count, Matrix, in_table, in_dist_field, cur_square, county_field):
    hyp_count = cur_count - np.count_nonzero(Matrix[dist1-1]) - np.count_nonzero(Matrix[dist2-1])
    hyp_square = cur_square - np.sum(np.square(Matrix[dist1-1])) - np.sum(np.square(Matrix[dist2-1]))
    Temp_Matrix = np.zeros([2,46], dtype=int)
    for d in range(2):
        for i in range(46):
            I = (i*2) + 1
            table_of_rows = [row[0] for row in arcpy.da.SearchCursor(in_table, ["Source_ID",in_dist_field,county_field], '''{}={} AND {}={}'''.format(in_dist_field,d+1,county_field,I))]
            Temp_Matrix[d][i] = len(table_of_rows)
    hyp_count += np.count_nonzero(Temp_Matrix[0]) + np.count_nonzero(Temp_Matrix[1])
    hyp_square += np.ndarray.sum(np.square(Temp_Matrix[0])) + np.ndarray.sum(np.square(Temp_Matrix[1])) 
    return(hyp_count, Temp_Matrix.copy(),hyp_square) 
    
def CountIntersections2(dist1, dist2, Matrix, G, distcount):
    HypMatrix = Matrix.copy()
    HypMatrix[dist1-1] = 0 #zeros out the dist1-1 row
    HypMatrix[dist2-1] = 0 #zeros out the dist2-1 row
    polys_in_dist1 = [node for node,y in G.nodes(data=True) if y["District Number"]==dist1] #Finds all polygons in district 1; creates list
    polys_in_dist2 = [node for node,y in G.nodes(data=True) if y["District Number"]==dist2] #Finds all polygons in district 2; creates list
    for p in polys_in_dist1:
        countynum = int(G.nodes[p]["County Number"]) #county number corresponding to the precinct in dist1
        HypMatrix[dist1-1][countynum] +=1 #Because county numbers are calculated with odd numbers only, we use (countynum-1)/2 for indexing
    for p in polys_in_dist2:
        countynum = int(G.nodes[p]["County Number"]) #county number corresponding to the precinct in dist2
        HypMatrix[dist2-1][countynum] +=1 #Because county numbers are calculated with odd numbers only, we use (countynum-1)/2 for indexing
    hypcount = np.count_nonzero(HypMatrix)-max(46,distcount) #Calculates the hypothetical number of nonzero entries in the Matrix. This is our number of CDIs
    #hypsquare = np.ndarray.sum(np.square(HypMatrix)) #Calculates the hypothetical sum of all squared entries in the Matrix. 
    hypexcess_GU_mat = [0]*max(distcount,46)
    transpose = HypMatrix.transpose()
    idx=0
    for col in transpose:
        maxval = max(col)
        hypexcess_GU_mat[idx] = sum(col)-maxval #Calculates the hypothetical excess_GU values for the Matrix. 
        idx+=1
    hypexcess_GU = sum(hypexcess_GU_mat)
    return(hypcount, HypMatrix, hypexcess_GU)


def arcprint(message,*variables):
    '''Prints a message using arcpy.AddMessage() unless it can't; then it uses print. '''
    if runspot == "ArcGIS":
        arcpy.AddMessage(message.format(*variables))
    elif runspot == "console":
        newmessage=message
        j=0
        while j<len(variables): #This while loop puts the variable(s) in the correct spot(s) in the string
            if type(variables[j]) == float:
                variables = list(variables)
                variables[j] = round(variables[j],3)
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
            if type(variables[j]) == float:
                variables = list(variables)
                variables[j] = round(variables[j],3)
            newmessage = newmessage.replace("{"+str(j)+"}",str(variables[j])) #Replaces {i} with the ith variable
            j=j+1
        raise RuntimeError(newmessage)
    else: 
        raise RuntimeError("No value for runspot has been assigned")

# START MAIN CODE
def main(*args):
    global runspot  #Allows runspot to be changed inside a function
    
    if sys.executable == r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe":  #Change this line if ArcGIS is located elsewhere
        runspot = "ArcGIS"
        arcprint("We are running this from inside ArcGIS")
    else:
        runspot = "console"
        arcprint("We are running this from the python console")   
            
    #Set environment settings
    
    currentdir = os.getcwd()
    path = currentdir + "\\SC_Redistricting_Updated.gdb"
    arcpy.env.workspace = path
    
    try:  #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
        in_table = sys.argv[1] 
        distcount = sys.argv[2]
        in_dist_field = sys.argv[3]
        county_field = sys.argv[4]
        num_counties = sys.argv[5]
    except IndexError: 
        try:  #Second, tries to take input from explicit input into main()
            in_table = args[0]  #out_table from main algorithm is sent into in_table
            distcount = args[1]
            in_dist_field = args[2]
            county_field = args[3]
            num_counties = args[4]
        except IndexError:  #Finally, manually assigns input values if they aren't provided
            in_table = path + "\\SC_Precincts_2021_v7_SA_7dists_10000"
            distcount = 7
            in_dist_field = "Dist_Assgn"
            county_field = "County_Num"
            num_counties = 46
            arcprint("We are using default input choices")
    
    #CDI = County-District-Intersection
    units_in_CDI = np.zeros([distcount, num_counties], dtype=int)
    
    #Adds 1 to the matrix element A[i,j] if there is a precinct in the ith district and jth county
    with arcpy.da.SearchCursor(in_table, [in_dist_field, county_field]) as cursor:
        for row in cursor:
            units_in_CDI[int(row[0]) - 1][int(row[1]) - 1] += 1
    
    CDI_Count = np.count_nonzero(units_in_CDI) - max(distcount, num_counties)
    
    #GU stands for Geographical Unit. In this loop, we count the number of GUs in each county that are not in the most prevalent district
    excess_GU_mat = [0] * max(distcount, num_counties)
    transpose = units_in_CDI.transpose()
    idx = 0
    for row in transpose:
        maxval = max(row)
        excess_GU_mat[idx] = sum(row) - maxval
        idx += 1
    excess_GU = sum(excess_GU_mat)
    
    return(units_in_CDI.copy(), CDI_Count, excess_GU)
    
#END FUNCTIONS    
if __name__ == "__main__":
    main()