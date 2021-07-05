# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 16:57:08 2021

@author: blake
"""

"The goal of this code is to create a random contiguous districting on the polygons given as input"

runspot="ArcGIS"

import arcpy, numpy, os

def arcprint(message,*variables):
    '''Prints a message using arcpy.AddMessage() unless it can't; then it uses print. '''
    if runspot == "ArcGIS":
        arcpy.AddMessage(message.format(*variables))
    else: 
        newmessage=message
        j=0
        while j<len(variables): #This while loop puts the variable(s) in the correct spot(s) in the string
            newmessage = newmessage.replace("{"+str(j)+"}",str(variables[j]))
            j=j+1
        print(newmessage)
        
def arcerror(message,*variables):
    '''Prints an error message using arcpy.AddError() unless it can't; then it uses print. '''
    if runspot == "ArcGIS":
        arcpy.AddError(message.format(*variables))
    else: 
        newmessage=message
        j=0
        while j<len(variables): #This while loop puts the variable(s) in the correct spot(s) in the string
            newmessage = newmessage.replace("{"+str(j)+"}",str(variables[j]))
            j=j+1
        raise NameError(newmessage)

### START MAIN CODE
# Set property to overwrite existing output, by default
arcpy.env.overwriteOutput = False

# Set environment settings
currentdir = os.getcwd()
path = currentdir + "\\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path

in_table = arcpy.GetParameterAsText(0) #Input Table
out_table = arcpy.GetParameterAsText(1) #Output Table
distnum = arcpy.GetParameterAsText(2) #Number of districts to create

distnum = round(float(distnum)) #Ensures that distnumber is an integer

#Generates a random number for each polygon
with arcpy.da.UpdateCursor(in_table, 'Test_val') as cursor:
    for row in cursor:
        row[0] = numpy.random.randint(100)
        cursor.updateRow(row)

#Creates a random contiguous districting with at least 300000 population each
# based on the values in Test_val
arcpy.stats.SpatiallyConstrainedMultivariateClustering(in_table,out_table,
                                                       "Test_val","ATTRIBUTE_VALUE",
                                                       "SUM_Popula",300000,None,
                                                       distnum,"CONTIGUITY_EDGES_ONLY")