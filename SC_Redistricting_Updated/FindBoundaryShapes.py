# -*- coding: utf-8 -*-
"""
Created on Thu May  6 17:21:17 2021

@author: blake
"""


import arcpy, os

def FindBoundaryShapes(in_table,neighbor_list,fields):
    print("Empty for now")

#FindNamingFields finds all fields that name or label a shape. 
def FindNamingFields(in_table):
    lstFields = arcpy.ListFields(in_table)
    namefields=[]
    distfields=[]
    for field in lstFields:
        if field.name in  ["GEOID20", "Name20", "NAME20", "Name", "FID"]:
            namefields.append(field.name)
        if field.name in ["CLUSTER_ID", "Dist_Assgn"]:
            distfields.append(field.name)
    return(namefields,distfields)


### START MAIN CODE
currentdir = os.getcwd()
arcpy.AddMessage("currentdir = {}".format(currentdir))
path = currentdir + "\\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path

in_table = arcpy.GetParameterAsText(0) #Input polygon file
#TypeOfNbr = arcpy.GetParameterAsText(1) #User input that declares whether we want district neighbors or shape neighbors

[namefields,distfields] = FindNamingFields(in_table)
all_fields = [item for sublist in [namefields, distfields] for item in sublist]
arcpy.AddMessage("namefields = {}".format(namefields))
arcpy.AddMessage("[namefields, distfields] = {}".format([namefields,distfields]))

if namefields == []:
    arcpy.AddMessage("Warning: the 'namefields' parameter is empty in PolygonNeighbors analysis.")
elif distfields == []:
    arcpy.AddMessage("Warning: the 'distfields' parameter is empty in PolygonNeighbors analysis.")

#Creates a neighbor list if one currently does not exist
neighbor_list = in_table + "_neighbor_list_shapes"
if not arcpy.Exists(neighbor_list):
    arcpy.PolygonNeighbors_analysis(in_table, neighbor_list, all_fields,None,None,None,"KILOMETERS")
    m = arcpy.mp.ArcGISProject("CURRENT").activeMap #Finds active map. 
    addTab = arcpy.mp.Table(path + "\\" + neighbor_list)
    m.addTable(addTab) #Adds table to Table of Contents
    
srcnamefields = namefields
nbrnamefields = namefields
srcdistfields = distfields
nbrdistfields = distfields

for field in srcnamefields:
    field = "src_" + field
    
for field in nbrnamefields:
    field = "nbr_" + field
    
for field in srcdistfields:
    field = "src_" + field
    
for field in nbrdistfields:
    field = "nbr_" + field
    
fieldList = arcpy.ListFields(in_table)    
fieldNames = [f.name for f in fieldList]

if "Boundary" not in fieldNames:
    arcpy.management.AddField(in_table, "Boundary", "SHORT")

# with arcpy.da.SearchCursor(neighborlist, [srcnamefields, nbrdistfields, "NODE_COUNT"], "NODE_COUNT=0") as cursor:
#     for row in cursor:
        
# with arcpy.da.UpdateCursor(in_table, [namefields, distfields, "Boundary"]) as cursor:
#     for row in cursor:
#         cursor.updateRow(row)


### THE ULTIMATE GOAL OF THIS CODE IS TO LIST ALL GEOGRAPHIC UNITS THAT ARE ON DISTRICT BOUNDARIES
