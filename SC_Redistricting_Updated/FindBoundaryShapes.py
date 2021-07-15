# -*- coding: utf-8 -*-
"""
Created on Thu May  6 17:21:17 2021

@author: blake
"""
runspot = "ArcGIS"
import arcpy, os, sys

def FindBoundaryShapes(in_table,neighbor_list,fields):
    print("Empty for now")

#FindNamingFields finds all fields that name or label a shape. 
def FindNamingFields(in_table):
    lstFields = arcpy.ListFields(in_table)
    namefields=[]
    distfields=[]
    breakflag=0
    for name in ["GEOID20", "OBJECTID", "FID", "SOURCE_ID"]:
        for field in lstFields:   
            if name ==field.name:
                namefields.append(name)
                breakflag=1
                break
        if breakflag==1:
            break
    #if field.name in  ["GEOID20", "Name20", "NAME20", "Name", "FID", "SOURCE_ID"]:
    breakflag=0
    for name in ["CLUSTER_ID", "Dist_Assgn"]:
        for field in lstFields:
            if name == field.name:
                distfields.append(name)
                breakflag=1
                break
        if breakflag==1:
            break
    return(namefields,distfields)

def MakeSQLExpression(in_row, fields4nbrlist,srclen,expression,comboexpression):          
#        arcprint("in_row[0] = {0}",in_row[0])
#        arcprint("in_row[1] = {0}",in_row[1])
        for i in range(srclen):
#            shape_name[i] = in_row[i]
#            arcprint("shape_name[{0}] = {1}",i,shape_name[i])
            if isinstance(in_row[i],str):
                expression[i] = "{0} = '{1}'".format(fields4nbrlist[i],in_row[i])
            else:
                expression[i] = "{0} = {1}".format(fields4nbrlist[i],in_row[i])
#            arcprint("expression[{0}] is {1}",i, expression[i])
            #Creates an SQL expression that is used in SearchCursor
            if i!=0:
                comboexpression = comboexpression + " AND " + expression[i]
            elif i==0:
                comboexpression = expression[i]
        return(comboexpression)
        
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
    
currentdir = os.getcwd()
path = currentdir + "\\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path

in_table = arcpy.GetParameterAsText(0) #Input polygon file
#TypeOfNbr = arcpy.GetParameterAsText(1) #User input that declares whether we want district neighbors or shape neighbors

if in_table == '':
    in_table = path + "\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1"
    runspot = "console"

[namefields,distfields] = FindNamingFields(in_table)
all_fields = [item for sublist in [namefields, distfields] for item in sublist]
#arcprint("namefields = {0}",namefields)
#arcprint("[namefields, distfields] = {0}"[namefields,distfields])

if namefields == []:
    arcprint("Warning: the 'namefields' parameter is empty in PolygonNeighbors analysis.")
if distfields == []:
    arcprint("Warning: the 'distfields' parameter is empty in PolygonNeighbors analysis.")

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
#    arcprint("field = {0}", field)
#    srcnamefields[0] 

srcnamefields = ["src_" + s for s in srcnamefields]
nbrnamefields = ["nbr_" + s for s in nbrnamefields]
srcdistfields = ["src_" + s for s in srcdistfields]
nbrdistfields = ["nbr_" + s for s in nbrdistfields]

#Finds number of srcnamefields
srclen = len(srcnamefields)
arcprint("srclen = {0}", srclen)

#Finds length of all field categories
nbrlen = len(nbrnamefields)
arcprint("nbrlen = {0}", nbrlen)
srcdistlen = len(srcdistfields)
arcprint("srcdistlen = {0}",srcdistlen)
nbrdistlen = len(nbrdistfields)
arcprint("nbrdistlen = {0}",nbrdistlen)

fieldList = arcpy.ListFields(in_table)    
fieldNames = [f.name for f in fieldList]

#src_string = "'" + "','".join(srcnamefields) + "'"
#arcprint("string = {0}",src_string)

if "Boundary" not in fieldNames:
    arcpy.management.AddField(in_table, "Boundary", "SHORT")

#Creates fields names for use in in_table cursor actions
fields4in_table = [namefields]
fields4in_table = [item for sublist in fields4in_table for item in sublist] #This line feels unnecessary?
fields4in_table.append("Boundary")
#arcprint("fields4in_table={0}",fields4in_table)
in_tab_len = len(fields4in_table)
#Creates field names for use in nbrlist cursor actions
fields4nbrlist = [srcnamefields, nbrnamefields, srcdistfields, nbrdistfields]
fields4nbrlist = [item for sublist in fields4nbrlist for item in sublist]
fields4nbrlist.append("NODE_COUNT")
#arcprint("fields4nbrlist={0}",fields4nbrlist)

shape_name = [0] * srclen
expression = [None] * srclen
comboexpression = None

#arcprint("[namefields, 'Boundary']={0}",[namefields, "Boundary"])
with arcpy.da.UpdateCursor(in_table, fields4in_table) as in_cursor:
    for in_row in in_cursor:
        in_row[in_tab_len -1]=0
        boundaryflag=0
        comboexpression = MakeSQLExpression(in_row, fields4nbrlist,srclen,expression,comboexpression)
        #arcprint("comboexpression is {0}",comboexpression)
        with arcpy.da.SearchCursor(neighbor_list, fields4nbrlist, comboexpression) as cursor:
            for row in cursor:   
                #arcprint("row[0] = {0} and row[srclen + nbrlen] = {1} and row[srclen + nbrlen + srcdistlen] = {2}",row[0],row[srclen+nbrlen], row[srclen + nbrlen + srcdistlen])
                if row[srclen + nbrlen] != row[srclen + nbrlen + srcdistlen]:
                    boundaryflag = 1 #shape is on a boundary
                    #arcprint("boundaryflag triggered when row[{0}] = {1} and row[{2}] = {3}",srclen+nbrlen, row[srclen+nbrlen], srclen + nbrlen + srcdistlen, row[srclen + nbrlen + srcdistlen])
                    break
        if boundaryflag ==1:
            in_row[in_tab_len-1]=1
        in_cursor.updateRow(in_row)


        



### THE ULTIMATE GOAL OF THIS CODE IS TO LIST ALL GEOGRAPHIC UNITS THAT ARE ON DISTRICT BOUNDARIES
