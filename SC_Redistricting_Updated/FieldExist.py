# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 14:35:12 2021

@author: blake
"""


runspot = "ArcGIS"

import arcpy,os,sys

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

### START MAIN CODE
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

sf="tl_2020_45_county20"
if arcpy.Exists(sf):
    lstFields = arcpy.ListFields(sf)
    
for field in lstFields:
    arcpy.AddMessage("{0} is a type of {1} with a length of {2}"
          .format(field.name, field.type, field.length))

