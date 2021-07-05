# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 14:35:12 2021

@author: blake
"""


runspot = "ArcGIS"

import arcpy,os

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

