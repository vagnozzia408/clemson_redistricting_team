# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 16:52:28 2021

@author: blake
"""
### IMPORTANT ASSUMPTION: WE ASSUME THAT THE FIRST COLUMN OF THE FEATURE LAYER
### IS AN ID COLUMN THAT UNIQUELY LABELS EACH ROW WITH THE NUMBERS 1-X, WHERE
### X IS THE NUMBER OF ROWS

#TO DO LIST
#1. Change argv stuff
#2. Consider new starting temperatures and whatnot
#3. Use build-balanced-zones
#4. Figure out what to do with x

import arcpy,math,os,sys
import random
#seed = 1738
#random.seed(seed)
import CreateSpanningTree

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
    """Returns a single positive integer that sums each district's deviation from the ideal population. Lower numbers for 'deviation' are better. A value of zero would indicate that every district has an equal number of people"""
    absdev = [0 for i in range(distcount)]
    
    for i in range(distcount):
        absdev[i] = abs(sumpop[i]-idealpop)
    deviation_ = sum(absdev)
    deviation_ = round(deviation_)
    return(deviation_)
        
def FindBoundaryShapes(in_table,neighbor_list):
    if neighbor_list == None:
        uniquename = arcpy.CreateUniqueName(in_table + "_neighbor_list")
        arcpy.PolygonNeighbors_analysis(in_table, uniquename,None,None,None,None,"KILOMETERS")
        
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
        
# Set environment settings
currentdir = os.getcwd()
path = currentdir + "\\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path

# CHANGE THIS 
in_table=arcpy.GetParameterAsText(0)
distcount=arcpy.GetParameterAsText(1)

# THIS TOO
if in_table == "" and distcount == "":
    in_table = path + "//SC_Counties_2020"
    distcount = "7"
    runspot = "console"
    arcprint("We are running this from the Spyder IDE.")

#User-defined variables
distcount = round(float(distcount))
T = 123000+149000 #Initial Temperature = stdev(pop) + mean pop 
MaxIter =500 #Maximum number of iterations to run


#Returns DistField "Dist_Assgn" and creates the field if it's not already there
DistField = FieldCheck(in_table)
#arcprint("DistField is {0}",DistField)


"""NEXT FEW LINES SHOULD BE CHANGED SO THAT RANDOM DISTRICTING IS RUN INSTEAD"""
#Generates random district assignments for each county
with arcpy.da.UpdateCursor(in_table, DistField) as cursor:
    for row in cursor:
        row[0] = random.randint(1,distcount)
        cursor.updateRow(row)
  
#Counts number of rows in in_table      
row_count = arcpy.GetCount_management(in_table).getOutput(0) #getOutput(0) returns the value at the first index position of a tool.
row_count=int(row_count)

#Finds field name for population
lstFields = arcpy.ListFields(in_table)
PopField = None
for field in lstFields:
    if field.name == "SUM_Popula" or field.name == "Precinct_P":
        PopField = field.name
        break
if PopField == None:
    arcerror("PopField is empty. Neither 'SUM_Popula' nor 'Precinct_P' were found as field names.")

#Finds sum of each district population
sumpop=[]
sumpop = [0]*distcount
with arcpy.da.SearchCursor(in_table, [PopField,DistField]) as cursor:
    for row in cursor:
        #i = district number minus 1, since district numbers range from 1 to 7
        i = row[1]-1
        i = int(i)
        sumpop[i] = row[0] + sumpop[i]
arcprint("The sum of polygon populations (i.e. sumpop) is {0}.",sumpop)
idealpop=sum(sumpop)/distcount    
deviation =[0]*(MaxIter+1)        
deviation[0] = DeviationFromIdealPop(sumpop, idealpop, distcount)

#Maybe delete x from below
[NameField,x] = FindNamingFields(in_table)
NameField = NameField[0]
arcprint("The NameField is '{0}'",NameField)
tol=30
hypsumpop=sumpop

#Starting the main line of the Simulated Annealing Algorithm
count = 0
while T>0.1 and count <MaxIter:
    arcprint("\ncount = {0}. About to add 1.",count)
    count = count+1
    """CURRENTLY, THIS CODE RANDOMLY SELECTS A SINGLE PRECINCT (OR COUNTY) AND RANDOMLY CHANGES ITS DISTRICT. WE NEED TO REPLACE THIS WITH RECOM"""
    dist1 = random.randint(1,distcount)
    dist2 = random.randint(1,distcount)
    while dist1==dist2: #Randomly selects two different districts
        dist1 = random.randint(1,distcount)
        dist2 = random.randint(1,distcount)
    arcprint("dist1 = {0} and dist2 = {1}.", dist1,dist2)
    try:
        [dist1_pop, dist2_pop,stateG] = CreateSpanningTree.main(path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1_neighbor_list_shapes", dist1, dist2, path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1",tol)
    except RuntimeError:
        arcprint("We had a runtime error. Selecting new districts")
        count=count-1
        continue
    if dist1_pop==float('inf') or dist2_pop==float('inf'):
        count=count-1
        continue
    hypsumpop[dist1-1] = dist1_pop
    hypsumpop[dist2-1] = dist2_pop
    deviation[count] = DeviationFromIdealPop(hypsumpop,idealpop,distcount)
    #arcprint("absolute deviation is {0}",deviation[count])    
    DeltaE = deviation[count] - deviation[count-1]
    arcprint("DeltaE = {0}. T = {1}",DeltaE,T)
    if DeltaE <0:
        sumpop=hypsumpop
        T = T*.999
        continue
    else :
        rand = random.uniform(0,1)
        try: 
            p = 1/math.exp(DeltaE/T)
        except OverflowError:
            p = 0
        arcprint("p = {0}. rand = {1}",p,rand)
        if rand<=p:
            sumpop=hypsumpop
            T = T*.999
            continue
        else: #undoes the district changes previously made. 
            count = count-1
    
    '''randshape = 45000
    adder = random.randint(0,45)
    randshape = randshape + adder*2+1
    #This cursor line updates one preinct at a time. 
    with arcpy.da.UpdateCursor(in_table, [NameField, DistField, PopField],"""{0}='{1}'""".format(NameField,randshape)) as cursor:
    #with arcpy.da.UpdateCursor(in_table, [NameField, DistField, PopField],"GEOID20 = '27'") as cursor:
        for row in cursor:
            currdist = int(row[1])
            distpop = row[2]
            #Ensures that the district assignment is actually changed
            while currdist == row[1]:
                row[1] = random.randint(1,distcount)
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
            T = T*.997
            continue
        else: #undoes the district changes previously made. 
            count = count-1
            sumpop[currdist-1] = sumpop[currdist-1] + distpop
            sumpop[newdist-1] = sumpop[newdist-1] - distpop
            with arcpy.da.UpdateCursor(in_table, [NameField, DistField, PopField],"{0} = '{1}'".format(NameField,randshape)) as cursor:
                for row in cursor:
                    row[1] = currdist
                    cursor.updateRow(row)'''
if T<=0.1:
    arcprint("\nSmallest legal temperature reached T = {0}.", T)
if count >=MaxIter:
    arcprint("Maximum number of iterations reached. count = {0} and MaxIter = {1}", count, MaxIter)
arcprint("Original deviation = {0}. Final deviation = {1}",deviation[2],deviation[MaxIter])
arcprint("sumpop is {0}",sumpop)
    
            