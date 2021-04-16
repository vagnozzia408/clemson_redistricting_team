# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 14:35:12 2021

@author: blake
"""


import arcpy
 
# Set environment settings
path = r"C:\Users\blake\Documents\Clemson Materials\Research\Saltzman Research\clemson_redistricting_team\SC_Redistricting_Updated\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path

sf="tl_2020_45_county20"
if arcpy.Exists(sf):
    lstFields = arcpy.ListFields(sf)
    
for field in lstFields:
    arcpy.AddMessage("{0} is a type of {1} with a length of {2}"
          .format(field.name, field.type, field.length))

