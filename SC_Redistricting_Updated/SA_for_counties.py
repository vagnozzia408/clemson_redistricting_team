# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 16:52:28 2021

@author: blake
"""


import arcpy,numpy,random,math

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

def DeviationFromIdealPop(sumpop):
    SPlength = len(sumpop)
    absdev = []
    absdev = [0 for i in range(SPlength)]
    
    idealpop= sum(sumpop)/SPlength
    for i in range(SPlength):
        absdev[i] = abs(sumpop[i]-idealpop)
    deviation = sum(absdev)
    deviation = round(deviation)
    return(deviation)
        
    
    
# Set environment settings
path = r"C:\Users\blake\Documents\Clemson Materials\Research\Saltzman Research\clemson_redistricting_team\SC_Redistricting_Updated\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path

in_table="tl_2020_45_county20"


#Returns DistField "Dist_Assgn" and creates the field if it's not already there
DistField = FieldCheck(in_table)

#Generates random district assignments for each county
with arcpy.da.UpdateCursor(in_table, [DistField]) as cursor:
    for row in cursor:
        row[0] = numpy.random.randint(1,8)
        cursor.updateRow(row)
  
#Counts number of rows in in_table      
rowcount = arcpy.GetCount_management(in_table)
arcpy.AddMessage("There are {0} rows in {1}".format(rowcount,in_table))

#Finds sum of each district population
sumpop=[]
sumpop = [0]*7
with arcpy.da.SearchCursor(in_table, ['SUM_Popula',DistField]) as cursor:
    for row in cursor:
        #i = district number minus 1, since district numbers range from 1 to 7
        i = row[1]-1
        i = int(i)
        sumpop[i] = row[0] + sumpop[i]
arcpy.AddMessage("sumpop is {0}".format(sumpop))            

T = 123000
count = 0
MaxIter =10000
deviation =[0]*(MaxIter+1)
deviation[0] = 10000000
while T>0.1 and count <MaxIter:
    arcpy.AddMessage("count = {}. About to add 1.".format(count))
    count = count+1
    #NEED TO FIX LINE BELOW. 46 SHOULD BE ROWCOUNT
    randshape = numpy.random.randint(0,46)
    with arcpy.da.UpdateCursor(in_table, ['FID', DistField, 'SUM_Popula'],"FID = {0}".format(randshape)) as cursor:
        for row in cursor:
            currdist = int(row[1])
            distpop = row[2]
            #Ensures that the district assignment is actually changed
            while currdist == row[1]:
                row[1] = numpy.random.randint(1,8)
            newdist = row[1]
            #subtracts population from district with fewer people
            sumpop[currdist-1] = sumpop[currdist-1] - distpop
            #adds population to district that just gained people
            sumpop[newdist-1] = sumpop[newdist-1] + distpop
            #arcpy.AddMessage("sumpop is {0}".format(sumpop)) 
            cursor.updateRow(row)   
    deviation[count] = DeviationFromIdealPop(sumpop)
    #arcpy.AddMessage("absolute deviation is {0}".format(deviation[count]))    
    DeltaE = deviation[count] - deviation[count-1]
    #arcpy.AddMessage("DeltaE = {0}. T = {1}".format(DeltaE,T))
    if DeltaE <0:
        T = T*.999
        continue
    else :
        rand = random.uniform(0,1)
        try: 
            p = 1/math.exp(DeltaE/T)
        except OverflowError:
            p = 0
        #arcpy.AddMessage("p = {0}. rand = {1}".format(p,rand))
        if rand>=p:
            T = T*.999
            continue
        else: #undoes the district changes previously made. 
            count = count-1
            sumpop[currdist-1] = sumpop[currdist-1] + distpop
            sumpop[newdist-1] = sumpop[newdist-1] - distpop
            with arcpy.da.UpdateCursor(in_table, ['FID', DistField, 'SUM_Popula'],"FID = {0}".format(randshape)) as cursor:
                for row in cursor:
                    row[1] = currdist
                    cursor.updateRow(row)

                
    
            