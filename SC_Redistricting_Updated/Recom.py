# -*- coding: utf-8 -*-
"""
Created on Tue May 25 14:48:33 2021

Recom

@author: blake & amy
"""

import arcpy, os


### START MAIN CODE
currentdir = os.getcwd()
path = currentdir + "\\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path

