# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 14:43:12 2021

@author: blake
"""


# Name: AddField_Example2.py
# Description: Add a pair of new fields to a table
 
# Import system modules
import arcpy, numpy
 
# Set environment settings
path = r"C:\Users\blake\Documents\Clemson Materials\Research\Saltzman Research\clemson_redistricting_team\SC_Redistricting_SCRATCH"
arcpy.env.workspace = path
 
# Set local variables
inFeatures = "tl_2020_45_county20"
fieldName1 = "Test_val"
fieldPrecision = 4
fieldAlias = "Test"

 
# Execute AddField for new field
arcpy.AddField_management(inFeatures, fieldName1, "LONG", fieldPrecision,
                          field_alias=fieldAlias, field_is_nullable="NULLABLE")
