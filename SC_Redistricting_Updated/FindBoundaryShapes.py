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
        #if field.name in  ["GEOID20", "Name20", "NAME20", "Name", "FID", "SOURCE_ID"]:
        if field.name in  ["GEOID20", "OBJECTID", "FID", "SOURCE_ID"]:
            namefields.append(field.name)
        if field.name in ["CLUSTER_ID", "Dist_Assgn"]:
            distfields.append(field.name)
    return(namefields,distfields)

def MakeSQLExpression(in_row, fields4nbrlist,srclen,expression,comboexpression):          
#        arcpy.AddMessage("in_row[0] = {}".format(in_row[0]))
#        arcpy.AddMessage("in_row[1] = {}".format(in_row[1]))
        for i in range(srclen):
#            shape_name[i] = in_row[i]
#            arcpy.AddMessage("shape_name[{0}] = {1}".format(i,shape_name[i]))
            if isinstance(in_row[i],str):
                expression[i] = "{0} = '{1}'".format(fields4nbrlist[i],in_row[i])
            else:
                expression[i] = "{0} = {1}".format(fields4nbrlist[i],in_row[i])
#            arcpy.AddMessage("expression[{0}] is {1}".format(i, expression[i]))
            #Creates an SQL expression that is used in SearchCursor
            if i!=0:
                comboexpression = comboexpression + " AND " + expression[i]
            elif i==0:
                comboexpression = expression[i]
        return(comboexpression)
        


### START MAIN CODE
currentdir = os.getcwd()
path = currentdir + "\\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path

in_table = arcpy.GetParameterAsText(0) #Input polygon file
#TypeOfNbr = arcpy.GetParameterAsText(1) #User input that declares whether we want district neighbors or shape neighbors

[namefields,distfields] = FindNamingFields(in_table)
all_fields = [item for sublist in [namefields, distfields] for item in sublist]
#arcpy.AddMessage("namefields = {}".format(namefields))
#arcpy.AddMessage("[namefields, distfields] = {}".format([namefields,distfields]))

if namefields == []:
    arcpy.AddMessage("Warning: the 'namefields' parameter is empty in PolygonNeighbors analysis.")
if distfields == []:
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

#for field in srcnamefields:
#    field = "src_" + field
#    arcpy.AddMessage("field = {}".format(field))
#    srcnamefields[0] 

srcnamefields = ["src_" + s for s in srcnamefields]
nbrnamefields = ["nbr_" + s for s in nbrnamefields]
srcdistfields = ["src_" + s for s in srcdistfields]
nbrdistfields = ["nbr_" + s for s in nbrdistfields]

#Finds number of srcnamefields
srclen = len(srcnamefields)
arcpy.AddMessage("srclen = {}".format(srclen))

#Finds length of all field categories
nbrlen = len(nbrnamefields)
arcpy.AddMessage("nbrlen = {}".format(nbrlen))
srcdistlen = len(srcdistfields)
arcpy.AddMessage("srcdistlen = {}".format(srcdistlen))
nbrdistlen = len(nbrdistfields)
arcpy.AddMessage("nbrdistlen = {}".format(nbrdistlen))

fieldList = arcpy.ListFields(in_table)    
fieldNames = [f.name for f in fieldList]

#src_string = "'" + "','".join(srcnamefields) + "'"
#arcpy.AddMessage("string = {}".format(src_string))

if "Boundary" not in fieldNames:
    arcpy.management.AddField(in_table, "Boundary", "SHORT")

#Creates fields names for use in in_table cursor actions
fields4in_table = [namefields]
fields4in_table = [item for sublist in fields4in_table for item in sublist] #This line feels unnecessary?
fields4in_table.append("Boundary")
arcpy.AddMessage("fields4in_table={}".format(fields4in_table))
in_tab_len = len(fields4in_table)
#Creates field names for use in nbrlist cursor actions
fields4nbrlist = [srcnamefields, nbrnamefields, srcdistfields, nbrdistfields]
fields4nbrlist = [item for sublist in fields4nbrlist for item in sublist]
fields4nbrlist.append("NODE_COUNT")
arcpy.AddMessage("fields4nbrlist={}".format(fields4nbrlist))

shape_name = [0] * srclen
expression = [None] * srclen
comboexpression = None

#arcpy.AddMessage("[namefields, 'Boundary']={}".format([namefields, "Boundary"]))
with arcpy.da.UpdateCursor(in_table, fields4in_table) as in_cursor:
    for in_row in in_cursor:
        in_row[in_tab_len -1]=0
        boundaryflag=0
        comboexpression = MakeSQLExpression(in_row, fields4nbrlist,srclen,expression,comboexpression)
        arcpy.AddMessage("comboexpression is {}".format(comboexpression))
        with arcpy.da.SearchCursor(neighbor_list, fields4nbrlist, comboexpression) as cursor:
            for row in cursor:   
                arcpy.AddMessage("row[0] = {0} and row[srclen + nbrlen] = {1} and row[srclen + nbrlen + srcdistlen] = {2}".format(row[0],row[srclen+nbrlen], row[srclen + nbrlen + srcdistlen]))
                if row[srclen + nbrlen] != row[srclen + nbrlen + srcdistlen]:
                    boundaryflag = 1 #shape is on a boundary
                    arcpy.AddMessage("boundaryflag triggered when row[{0}] = {1} and row[{2}] = {3}".format(srclen+nbrlen, row[srclen+nbrlen], srclen + nbrlen + srcdistlen, row[srclen + nbrlen + srcdistlen]))
                    break
        if boundaryflag ==1:
            in_row[in_tab_len-1]=1
        in_cursor.updateRow(in_row)


        



### THE ULTIMATE GOAL OF THIS CODE IS TO LIST ALL GEOGRAPHIC UNITS THAT ARE ON DISTRICT BOUNDARIES
