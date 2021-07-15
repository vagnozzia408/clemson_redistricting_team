# -*- coding: utf-8 -*-
"""
Created on Mon Jul 12 19:39:42 2021

@author: blake
"""
runspot = None

import arcpy,os
import CreateSpanningTree

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

currentdir = os.getcwd()
path = currentdir + "\\SC_Redistricting_Updated.gdb"

runspot = "console"
arcprint("This is an example of how to run python script from another python script. This is test1.py")

[dist1_pop, dist2_pop] = CreateSpanningTree.main(path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1_neighbor_list_shapes", 1, 3, path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1",30)