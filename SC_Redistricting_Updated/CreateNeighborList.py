# -*- coding: utf-8 -*-
"""
Created on Thu May  6 17:21:17 2021

@author: Blake Splitter
"""
import arcpy, os, sys
import random
seed = 1738

#FindNamingFields finds a field that names or labels a shape. 
def FindNamingFields(in_table):
    lstFields = arcpy.ListFields(in_table)
    namefield = None
    distfield = None
    breakflag = 0
    for name in ["GEOID20", "OBJECTID", "FID", "SOURCE_ID"]:
        for field in lstFields:   
            if name == field.name:
                namefield = name
                breakflag = 1
                break
        if breakflag == 1:
            break
    if namefield == None:
        arcerror("No value for namefield was found.")
    breakflag = 0

    for name in ["CLUSTER_ID", "ZONE_ID"]:
        for field in lstFields:
            if name == field.name:
                distfield = name
                breakflag = 1
                break
        if breakflag == 1:
            break
    if distfield == None:
        arcerror("No value for distfield was found. All polygons must be assigned a district in a field labeled 'CLUSTER_ID' or 'ZONE_ID'.")
    return(namefield, distfield)

def MakeSQLExpression(in_row, fields4nbrlist):          
    comboexpression=None
    expression = [None]
#        arcprint("in_row[0] = {0}",in_row[0])
#        arcprint("in_row[1] = {0}",in_row[1]
    for i in range(1):
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
            if type(variables[j]) == float:
                variables = list(variables)
                variables[j] = round(variables[j],3)
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
            if type(variables[j]) == float:
                variables = list(variables)
                variables[j] = round(variables[j],3)
            newmessage = newmessage.replace("{"+str(j)+"}",str(variables[j])) #Replaces {i} with the ith variable
            j=j+1
        raise RuntimeError(newmessage)
    else: 
        raise RuntimeError("No value for runspot has been assigned")


### START MAIN CODE
def main(*args):
    global runspot
    
    if sys.executable == r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe": #Change this line if ArcGIS is located elsewhere
        runspot = "ArcGIS"
        arcprint("We are running FindBoundaryShapes from inside ArcGIS")
    else:
        runspot = "console"
        arcprint("\nWe are running FindBoundaryShapes from the python console")
        
    currentdir = os.getcwd()
    path = currentdir + "\\SC_Redistricting_Updated.gdb"
    arcpy.env.workspace = path
    
    arcpy.env.overwriteOutput = True
    
    try: #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
        in_table = sys.argv[1]
    except IndexError: 
        try: #Second, tries to take input from explicit input into main()
            in_table = args[0]
            arcprint("Running CreateNeighborList using input from another script")
        except IndexError: #Finally, manually assigns input values if they aren't provided
            in_table = path + "\\Precincts_2020"
            arcprint("Running CreateNeighborList using default input choices")
    
    #Finds the name field and distfield for the in_table
    [namefield,distfield] = FindNamingFields(in_table)
    
    if namefield == []:
        arcerror("Error: the 'namefield' parameter is empty in PolygonNeighbors analysis.")
    if distfield == []:
        arcerror("Error: the 'distfield' parameter is empty in PolygonNeighbors analysis.")
    
    #Creates a neighbor list if one currently does not exist
    neighbor_list = in_table + "_nbr_list"

#    if arcpy.Exists(neighbor_list) == False:
    arcpy.PolygonNeighbors_analysis(in_table, neighbor_list, [namefield, distfield], None, None, None, "KILOMETERS")

###EVERYTHING BELOW THIS LINE ATTEMPTS TO FIND WHICH POLYGONS ARE ON DISTRICT BOUNDARIES, WHICH IS NO LONGER NEEDED
#    srcnamefield = "src_" + namefield
#    nbrnamefield = "nbr_" + namefield
#    srcdistfield = "src_" + distfield
#    nbrdistfield = "nbr_" + distfield
#
#    fieldList = arcpy.ListFields(in_table)    
#    fieldNames = [f.name for f in fieldList]
#    
#    if "Boundary" not in fieldNames:
#        arcpy.management.AddField(in_table, "Boundary", "SHORT")
#    
#    #Creates fields names for use in in_table cursor actions
#    fields4in_table = [namefield, "Boundary"]
#    
#    #Creates field names for use in nbrlist cursor actions
#    fields4nbrlist = [srcnamefield, nbrnamefield, srcdistfield, nbrdistfield]
#    fields4nbrlist.append("NODE_COUNT")
#
#    #Finds all units that are on a boundary
#    with arcpy.da.UpdateCursor(in_table, fields4in_table) as in_cursor:
#        for in_row in in_cursor:
#            in_row[1]=0 #Boundary = 0
#            boundaryflag=0
#            #SQLexpression = MakeSQLExpression(in_row, fields4nbrlist)
#            SQLexpression = "{0} = {1}".format(srcnamefield,in_row[0])
#            #arcprint("SQLexpression is {0}",SQLexpression)
#            with arcpy.da.SearchCursor(neighbor_list, fields4nbrlist, SQLexpression) as cursor:
#                for row in cursor:   
#                    if row[2] != row[3]: #src_Cluster_ID != nbr_Cluster_ID
#                        boundaryflag = 1 #shape is on a boundary
#                        break
#            if boundaryflag ==1:
#                in_row[1]=1
#            in_cursor.updateRow(in_row)
    
    if __name__ != "__main__":
        return(neighbor_list)
    
if __name__ == "__main__":
    main()
