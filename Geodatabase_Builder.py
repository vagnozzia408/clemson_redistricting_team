# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 14:01:29 2021

@author: blake
"""


import os, arcpy
def gdbbuilder(gdbnames):
    arcpy.AddMessage("Starting Geodatabase Builder")
    currentdir = os.getcwd()
    projectname = currentdir.split("\\")[-1]  
    for gdbname in gdbnames.split(";"):
        newgdbname = "{}_{}".format(projectname,gdbname)
        arcpy.management.CreateFileGDB(currentdir,newgdbname, "CURRENT")
    
gdbnames = arcpy.GetParameterAsText(0)

gdbbuilder(gdbnames)