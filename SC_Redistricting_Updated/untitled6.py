# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 16:57:08 2021

@author: blake
"""


import arcpy, numpy

# Set environment settings
path = r"C:\Users\blake\Documents\Clemson Materials\Research\Saltzman Research\clemson_redistricting_team\SC_Redistricting_Updated\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path

in_table = 