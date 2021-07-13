# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 16:52:28 2021

@author: blake
"""
### IMPORTANT ASSUMPTION: WE ASSUME THAT THE FIRST COLUMN OF THE FEATURE LAYER
### IS AN ID COLUMN THAT UNIQUELY LABELS EACH ROW WITH THE NUMBERS 1-X, WHERE
### X IS THE NUMBER OF ROWS

import arcpy,numpy,random,math,sys,os

runspot = "ArcGIS"

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
        
def arcprint(message,*variables):
    '''Prints a message using arcpy.AddMessage() unless it can't; then it uses print. '''
    if runspot == "ArcGIS":
        arcpy.AddMessage(message.format(*variables))
    else:
        newmessage=message
        j=0
        while j<len(variables): #This while loop puts the variable(s) in the correct spot(s) in the string
            newmessage = newmessage.replace("{"+str(j)+"}",str(variables[j])) #Replaces {i} with the ith variable
            j=j+1
        print(newmessage)

def arcerror(message,*variables):
    '''Prints an error message using arcpy.AddError() unless it can't; then it uses print. '''
    if runspot == "ArcGIS":
        arcpy.AddError(message.format(*variables))
    else:
        newmessage=message
        j=0
        while j<len(variables): #This while loop puts the variable(s) in the correct spot(s) in the string
            newmessage = newmessage.replace("{"+str(j)+"}",str(variables[j])) #Replaces {i} with the ith variable
            j=j+1
        raise RuntimeError(newmessage)

### START MAIN CODE
# Set environment settings
currentdir = os.getcwd()
path = currentdir + "\\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path

in_table=arcpy.GetParameterAsText(0)
distcount=arcpy.GetParameterAsText(1)

if in_table == "" and distcount == "":
    in_table = path + "//SC_Counties_2020"
    distcount = "7"
    runspot = "console"
    arcprint("We are running this from the Spyder IDE.")

#User-defined variables
distcount = round(float(distcount))
T = 123000+149000 #Initial Temperature = stdev(pop) + mean pop 
MaxIter =1000 #Maximum number of iterations to run


#Returns DistField "Dist_Assgn" and creates the field if it's not already there
DistField = FieldCheck(in_table)
arcprint("DistField is {0}",DistField)

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
    arcerror("popfield is empty. Neither 'SUM_Popula' nor 'Precinct_P' were found as field names.")

#Finds sum of each district population
sumpop=[]
sumpop = [0]*distcount
with arcpy.da.SearchCursor(in_table, [popfield,DistField]) as cursor:
    for row in cursor:
        #i = district number minus 1, since district numbers range from 1 to 7
        i = row[1]-1
        i = int(i)
        sumpop[i] = row[0] + sumpop[i]
arcprint("sumpop is {0}",sumpop)
idealpop=sum(sumpop)/distcount    
deviation =[0]*(MaxIter+1)        
deviation[0] = DeviationFromIdealPop(sumpop, idealpop, distcount)

lstFields = arcpy.ListFields(in_table)
ObjectID = lstFields[0].name
arcprint("ObjectID = {0}",ObjectID)

count = 0
while T>0.1 and count <MaxIter:
    arcprint("count = {0}. About to add 1.",count)
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
            #arcprint("sumpop is {0}",sumpop) 
            cursor.updateRow(row)   
    deviation[count] = DeviationFromIdealPop(sumpop,idealpop,distcount)
    #arcprint("absolute deviation is {0}",deviation[count])    
    DeltaE = deviation[count] - deviation[count-1]
    arcprint("DeltaE = {0}. T = {1}",DeltaE,T)
    if DeltaE <0:
        T = T*.997
        continue
    else :
        rand = random.uniform(0,1)
        try: 
            p = 1/math.exp(DeltaE/T)
        except OverflowError:
            p = 0
        arcprint("p = {0}. rand = {1}",p,rand)
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
arcprint("Original deviation = {0}. Final deviation = {1}",deviation[2],deviation[MaxIter])
arcprint("sumpop is {0}",sumpop)
    
            