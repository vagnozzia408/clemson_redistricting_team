# -*- coding: utf-8 -*-
"""
Created on Fri Jul 23 13:04:43 2021

@author: Blake Splitter and Amy Burton
"""

import arcpy,os, sys
#import CreateSpanningTree
#import numpy as np
import math
#from arcpy.sa import *

class District:
    Area = 0
    Perimeter = 0
    ppCompactScore = 0
    Units = [] #This list will need to contain a list of IDs corresponding to the units currently in the district, may be redundant
    NumUnits = 0
    VoteCountRed = 0
    VoteCountBlue = 0
    EfficencyGap = 0 #This will be terms of the dist: wastedRed votes in this district - wastedblue votes in this district, divided by total number of votes
    Original = True
    
    def __init__(self, ID):
        self.ID = ID
    
    def UpdateStats(self, a, p, ppc):
        self.Area = a
        self.Perimeter = p
        self.ppCompactScore = ppc
        
    def UpdateCMPStats(self, eg):
        self.EfficencyGap = eg
        
def PolsbyPopperUpdate(dist1, dist2,shapefile, path, DistrictList):
    #Create a Reduced Shapefile just based on dist1 and dist2, and update the appropriate districts in DistrictList
    inZoneData = shapefile
    zoneField = "Cluster_ID"
    outTable = path + "\\TempDistrictZonalGeometry"
    #cellSize = 1.28781240014216E-02
    arcpy.CheckOutExtension("Spatial")
    arcpy.sa.ZonalGeometryAsTable(inZoneData, zoneField, outTable)
    with arcpy.da.SearchCursor(outTable, "*", '''{}={} OR {}={}'''.format("Value",dist1,"Value",dist2)) as cursor:
        for row in cursor:
            DistrictList[row[1]-1].UpdateStats(row[2], row[3], 4*math.pi*float(row[2])/float(row[3])**2)
            DistrictList[row[1]-1].Original = False
    return DistrictList


def CompetitionUpdate(dist1, dist2, DistrictList):
    DistrictList[dist1 - 1].VoteCountRed = 0
    DistrictList[dist1 - 1].VoteCountBlue = 0
    DistrictList[dist2 - 1].VoteCountRed = 0
    DistrictList[dist2 - 1].VoteCountBlue = 0
    with arcpy.da.SearchCursor(shapefile, ["SOURCE_ID", "Cluster_ID", "Vote_Red", "Vote_Blue"], '''{}={} OR {}={}'''.format("Cluster_ID",dist1,"Cluster_ID",dist2)) as cursor:
        for row in cursor:
            DistrictList[row[1] - 1].VoteCountRed += row[2]
            DistrictList[row[1] - 1].VoteCountBlue += row[3]
    wastedRed = 0
    wastedBlue = 0
    EG = 0
    dis = DistrictList[dist1-1]
    if dis.VoteCountRed > dis.VoteCountBlue:
        wastedRed = (dis.VoteCountRed - dis.VoteCountBlue)/2
        wastedBlue = dis.VoteCountBlue
    else :
        wastedBlue = (dis.VoteCountBlue - dis.VoteCountRed)/2
        wastedRed = dis.VoteCountRed
    EG = (wastedRed - wastedBlue) / (dis.VoteCountRed+dis.VoteCountBlue)
    dis.UpdateCMPStats(EG)
    dis = DistrictList[dist2-1]
    if dis.VoteCountRed > dis.VoteCountBlue:
        wastedRed = (dis.VoteCountRed - dis.VoteCountBlue)/2
        wastedBlue = dis.VoteCountBlue
    else :
        wastedBlue = (dis.VoteCountBlue - dis.VoteCountRed)/2
        wastedRed = dis.VoteCountRed
    EG = (wastedRed - wastedBlue) / (dis.VoteCountRed+dis.VoteCountBlue)
    dis.UpdateCMPStats(EG)
    return DistrictList

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
        
def main(*args):
    ### MAIN CODE STARTS HERE
    #global DistrictList
    global runspot #Allows runspot to be changed inside a function
    
    if sys.executable == r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe": #Change this line if ArcGIS is located elsewhere
        runspot = "ArcGIS"
        if __name__ == "__main__":
            arcprint("We are running this from inside ArcGIS")
    else:
        runspot = "console"
        if __name__=="__main__":
            arcprint("We are running this from the python console")
    
    currentdir = os.getcwd()
    path = currentdir + "\\SC_Redistricting_Updated.gdb"
    arcpy.env.workspace=path
    arcpy.env.overwriteOutput=True
    
    try: #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
        shapefile=sys.argv[1]
        zoneField = sys.argv[2]
        ###NEED TO ADD stateG HERE SOMEHOW
    except IndexError: 
        try: #Second, tries to take input from explicit input into main()
            shapefile = args[0]
            zoneField = args[1]
        except IndexError: #Finally, manually assigns input values if they aren't provided
            shapefile=path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1"
            zoneField = "Cluster_ID"
            arcprint("We are using default input choices for GraphMeasures.py")

    # Run Compactness Scores the first time and list the list DistrictList
    inZoneData = shapefile # The major change for the in-iteration calculation is to only input a part of this table, dealing with dist1 and dist2.
    outTable = path + "\\DistrictZonalGeometry2"
    #cellSize = 1
    arcpy.CheckOutExtension("Spatial")
    DistrictList = []  
    arcprint("This is line 94")
    arcpy.sa.ZonalGeometryAsTable(inZoneData, zoneField, outTable)
    arcprint("This is line 96")
    with arcpy.da.SearchCursor(outTable, "*", "*") as cursor:
        for row in cursor:
            DistrictList.append(District(row[1]))
            DistrictList[-1].UpdateStats(row[2], row[3], 4*math.pi*float(row[2])/float(row[3])**2)
    
#    with arcpy.da.SearchCursor(shapefile, ["SOURCE_ID", "Cluster_ID", "Vote_Red", "Vote_Blue"], "*") as cursor:
#        for row in cursor:
#            DistrictList[row[1] - 1].VoteCountRed += row[2]
#            DistrictList[row[1] - 1].VoteCountBlue += row[3]
#    
#    wastedRed = 0
#    wastedBlue = 0
#    EG = 0
#    for dis in DistrictList:
#        if dis.VoteCountRed > dis.VoteCountBlue:
#            wastedRed = (dis.VoteCountRed - dis.VoteCountBlue)/2
#            wastedBlue = dis.VoteCountBlue
#        else :
#            wastedBlue = (dis.VoteCountBlue - dis.VoteCountRed)/2
#            wastedRed = dis.VoteCountRed
#        EG = (wastedRed - wastedBlue) / (dis.VoteCountRed+dis.VoteCountBlue)
#        dis.UpdateCMPStats(EG)
        
        
    return(DistrictList)
        
if __name__ == "__main__":
    main()