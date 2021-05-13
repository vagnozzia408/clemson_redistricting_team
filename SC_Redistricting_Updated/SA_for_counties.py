# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 16:52:28 2021

@author: blake
"""
### IMPORTANT ASSUMPTION: WE ASSUME THAT THE FIRST COLUMN OF THE FEATURE LAYER
### IS AN ID COLUMN THAT UNIQUELY LABELS EACH ROW WITH THE NUMBERS 1-X, WHERE
### X IS THE NUMBER OF ROWS

import arcpy,numpy,random,math,sys

def FieldCheck(in_table):
    lstFields = arcpy.ListFields(in_table)
    DistField = "Dist_Assgn"
    x = False
    for field in lstFields:
        if field.name == "Dist_Assgn":
            x = True
    if x != True:
        arcpy.AddMessage("Field does not exist. Adding Dist_Assgn")
        arcpy.AddField_management(in_table, "Dist_Assgn", "DOUBLE", field_alias="DIST_ASSIGNMENT")
    return(DistField)    

def DeviationFromIdealPop(sumpop,idealpop,distcount):
    absdev = [0 for i in range(distcount)]
    
    for i in range(distcount):
        absdev[i] = abs(sumpop[i]-idealpop)
    deviation = sum(absdev)
    deviation = round(deviation)
    return(deviation)
        
def FindBoundaryShapes(in_table,neighbor_list):
    if neighbor_list == None:
        uniquename = arcpy.CreateUniqueName(in_table + "_neighbor_list")
        arcpy.PolygonNeighbors_analysis(in_table, uniquename,None,None,None,None,"KILOMETERS")

### START MAIN CODE
# Set environment settings
path = r"C:\Users\blake\Documents\Clemson Materials\Research\Saltzman Research\clemson_redistricting_team\SC_Redistricting_Updated\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path

in_table=arcpy.GetParameterAsText(0)

#User-defined variables
distcount=arcpy.GetParameterAsText(1)
distcount = round(float(distcount))
T = 123000+149000 #Initial Temperature = stdev(pop) + mean pop 
MaxIter =1000 #Maximum number of iterations to run


#Returns DistField "Dist_Assgn" and creates the field if it's not already there
DistField = FieldCheck(in_table)
arcpy.AddMessage("DistField is {}".format(DistField))

#Generates random district assignments for each county
with arcpy.da.UpdateCursor(in_table, DistField) as cursor:
    for row in cursor:
        row[0] = numpy.random.randint(1,distcount+1)
        cursor.updateRow(row)
  
#Counts number of rows in in_table      
row_count = arcpy.GetCount_management(in_table).getOutput(0) #getOutput(0) returns the value at the first index position of a tool.

#Finds field name for population
lstFields = arcpy.ListFields(in_table)
popfield = None
for field in lstFields:
    if field.name == "SUM_Popula" or field.name == "Precinct_P":
        popfield = field.name
if popfield == None:
    arcpy.AddMessage("popfield is empty. Neither 'SUM_Popula' nor 'Precinct_P' were found as field names.")
    sys.exit()

#Finds sum of each district population
sumpop=[]
sumpop = [0]*distcount
with arcpy.da.SearchCursor(in_table, [popfield,DistField]) as cursor:
    for row in cursor:
        #i = district number minus 1, since district numbers range from 1 to 7
        i = row[1]-1
        i = int(i)
        sumpop[i] = row[0] + sumpop[i]
arcpy.AddMessage("sumpop is {0}".format(sumpop))
idealpop=sum(sumpop)/distcount    
deviation =[0]*(MaxIter+1)        
deviation[0] = DeviationFromIdealPop(sumpop, idealpop, distcount)

lstFields = arcpy.ListFields(in_table)
ObjectID = lstFields[0].name
arcpy.AddMessage("ObjectID = {}".format(ObjectID))

count = 0
while T>0.1 and count <MaxIter:
    arcpy.AddMessage("count = {}. About to add 1.".format(count))
    count = count+1
    randshape = numpy.random.randint(0,row_count)
    with arcpy.da.UpdateCursor(in_table, [ObjectID, DistField, popfield],"{0} = {1}".format(ObjectID,randshape)) as cursor:
        for row in cursor:
            currdist = int(row[1])
            distpop = row[2]
            #Ensures that the district assignment is actually changed
            while currdist == row[1]:
                row[1] = numpy.random.randint(1,distcount+1)
            newdist = row[1]
            #subtracts population from district with fewer people
            sumpop[currdist-1] = sumpop[currdist-1] - distpop
            #adds population to district that just gained people
            sumpop[newdist-1] = sumpop[newdist-1] + distpop
            #arcpy.AddMessage("sumpop is {0}".format(sumpop)) 
            cursor.updateRow(row)   
    deviation[count] = DeviationFromIdealPop(sumpop,idealpop,distcount)
    #arcpy.AddMessage("absolute deviation is {0}".format(deviation[count]))    
    DeltaE = deviation[count] - deviation[count-1]
    arcpy.AddMessage("DeltaE = {:.2f}. T = {:.2f}".format(DeltaE,T))
    if DeltaE <0:
        T = T*.997
        continue
    else :
        rand = random.uniform(0,1)
        try: 
            p = 1/math.exp(DeltaE/T)
        except OverflowError:
            p = 0
        arcpy.AddMessage("p = {:.4f}. rand = {:.4f}".format(p,rand))
        if rand<=p:
            T = T*.999
            continue
        else: #undoes the district changes previously made. 
            count = count-1
            sumpop[currdist-1] = sumpop[currdist-1] + distpop
            sumpop[newdist-1] = sumpop[newdist-1] - distpop
            with arcpy.da.UpdateCursor(in_table, [ObjectID, DistField, popfield],"{0} = {1}".format(ObjectID,randshape)) as cursor:
                for row in cursor:
                    row[1] = currdist
                    cursor.updateRow(row)
arcpy.AddMessage("Original deviation = {}. Final deviation = {}".format(deviation[2],deviation[MaxIter]))
arcpy.AddMessage("sumpop is {}".format(sumpop))
    
            