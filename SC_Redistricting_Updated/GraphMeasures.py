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
    WastedRed = 0
    WastedBlue = 0
    BlueShare = 0
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
    
class Map:
    ItNum = 0
    AvgPPCompactScore = 0
    WastedVotesRed = 0
    WastedVotesBlue = 0
    TotalRedVotes = 0
    TotalBlueVotes = 0 
    EG = 0 
    Variance = 0
    MedianMean = 0
    BG_Modified = 0
    
    def __init__(self, itNum):
        self.ItNum = itNum
    
    def UpdateMapStats(self, DistrictList):
        totalpp = 0
        # Runs through districtList to create AvgppCompactScore and EG and Median_Mean
        AshareCpy = []
        meansq = 0
        mean = 0
        for dis in DistrictList:
            totalpp += dis.ppCompactScore
            self.TotalRedVotes += dis.VoteCountRed
            self.TotalBlueVotes += dis.VoteCountBlue
            self.WastedVotesRed += dis.WastedRed
            self.WastedVotesBlue += dis.WastedBlue
            dis.BlueShare = dis.VoteCountBlue / (dis.VoteCountRed + dis.VoteCountBlue)
            AshareCpy.append(dis.BlueShare)
            meansq += pow(dis.BlueShare, 2)
            mean += dis.BlueShare
        self.AvgPPCompactScore = totalpp / len(DistrictList)
        self.EG = (self.WastedVotesRed - self.WastedVotesBlue) / (self.TotalRedVotes + self.TotalBlueVotes) 
        middle = int((len(DistrictList) + 1)/ 2) # top median
        AshareCpy.sort()
        meansq = meansq/len(DistrictList)
        mean = mean / len(DistrictList)
        self.Variance = meansq - pow(mean,2)
        if len(DistrictList) % 2 == 0:
            median = (AshareCpy[middle] + AshareCpy[middle-1] ) / 2
        else :
            median = AshareCpy[middle - 1]
        mean = (self.TotalRedVotes + self.TotalBlueVotes) / len(DistrictList)
        self.MedianMean = mean - median
        
        #This code is in the works, and may not possibly work as well. but here are my first attempts:
        
        # BG_Modified (done from Ashare: Democratic Vote Shares per District)
        V = self.TotalBlueVotes / len(DistrictList)
        V_Points = [0] * (2*len(DistrictList))
        V_Points[0] = V
        for i in range(0, len(DistrictList)):
            new_v = 0
            if DistrictList[i].BlueShare < 0.5:
                new_v = 1 - (1-V)/(2*(1-DistrictList[i].BlueShare))
            else :
                new_v = V / (2*DistrictList[i].BlueShare)
            V_Points[i+1] = new_v
        V_Points_frontSort = V_Points[:len(DistrictList)+1]
        V_Points_frontSort.sort()
        V_Points[:len(DistrictList) + 1] = V_Points_frontSort
        SV_Points = [0] * (2*len(DistrictList))
        for i in range(0, len(DistrictList)):
            SV_Points[i] = i / len(DistrictList)
        for i in range(0, len(DistrictList)):
            if V_Points[i] == V_Points[i+1]: # if we observe two consecutive V_Points
                if i == len(DistrictList) - 1: # if the last two points are consecutive
                    m = (SV_Points[i+1] - SV_Points[i-1])/(V_Points[i+1] - V_Points[i-1])
                    b = SV_Points[i-1] - m*V_Points[i-1]
                    adj_V = (SV_Points[i]-b)/m
                    if adj_V > V_Points[i-1] and adj_V < V_Points[i+1] :
                        V_Points[i] = adj_V
                else: # if the two consective points are NOT the last two
                    m = (SV_Points[i+2] - SV_Points[i])/(V_Points[i+2]-V_Points[i])
                    b = SV_Points[i] - (m*V_Points[i])
                    adj_V = (SV_Points[i+1]-b) / m
                    if adj_V > V_Points[i] and adj_V < V_Points[i+2] :
                        V_Points[i+1] = adj_V
            # Otherwise do nothing
        IV_Points = [0] * (2*len(DistrictList))
        ISV_Points = [0] * (2*len(DistrictList))
        for i in range(0, len(DistrictList)):
            IV_Points[i] = 1 - V_Points[len(DistrictList) - i]
            ISV_Points[i] = 1 - SV_Points[len(DistrictList) - i]
        k = 0
        for i in range(0, len(DistrictList) - 1):
            if ((V_Points[i] < IV_Points[i]) and (V_Points[i+1] > IV_Points[i+1])) or ((V_Points[i] > IV_Points[i]) or (V_Points[i+1] < IV_Points[i+1])) :
                m1 = (SV_Points[i+1] - SV_Points[i])/(V_Points[i+1]-V_Points[i])  # DIVISION BY ZERO HAPPENS HERE. How do we get two consecutive V_Points???
                b1 = SV_Points[i] - m1*V_Points[i]
                # Inverted Seats-Vote Line Segment
                m2 = (ISV_Points[i+1] - ISV_Points[i])/(IV_Points[i+1]-IV_Points[i])
                b2 = ISV_Points[i] - m2*IV_Points[i]
                # Intersection Point
                x = (b2-b1)/(m1-m2)
                y = m1 * x + b1
                # Add the intersection point.
                V_Points[len(DistrictList)+k+1] = x
                IV_Points[len(DistrictList)+k+1] = x
                SV_Points[len(DistrictList)+k+1] = y
                ISV_Points[len(DistrictList)+k+1] = y
                k += 1
        V_Points = V_Points[:len(DistrictList)+k+1]
        V_Points.sort()
        SV_Points = SV_Points[:len(DistrictList)+k+1]
        SV_Points.sort()
        IV_Points = IV_Points[:len(DistrictList)+k+1]
        IV_Points.sort()
        ISV_Points = ISV_Points[:len(DistrictList)+k+1]
        ISV_Points.sort()
        
        modified_geom_bias = 0
        xmax = max(V_Points[len(DistrictList) + k], IV_Points[len(DistrictList) + k])
        
        for i in range(0, len(DistrictList) + k) :
            # Area under Sears-Vote Curve using trapezoids
            b1 = xmax - V_Points[i]
            b2 = xmax - V_Points[i+1]
            h = SV_Points[i+1] - SV_Points[i]
            area1 = 0.5 * (b1+b2) * h
            # Area under Inverted Sears-Vote Curve.
            ib1 = xmax - IV_Points[i]
            ib2 = xmax - IV_Points[i+1]
            ih = ISV_Points[i+1] - ISV_Points[i]
            area2 = 0.5 * (ib1+ib2) * ih
            
            modified_geom_bias += abs(area2-area1)
        self.BG_Modified = modified_geom_bias
        
        
def PolsbyPopperUpdate(dist1, dist2,shapefile, path, DistrictList,zoneField):
    #Create a Reduced Shapefile just based on dist1 and dist2, and update the appropriate districts in DistrictList
    inZoneData = shapefile
    #zoneField = "Cluster_ID"
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

    dis = DistrictList[dist1-1]
    if dis.VoteCountRed > dis.VoteCountBlue:
        dis.WastedRed = (dis.VoteCountRed - dis.VoteCountBlue)/2
        dis.WastedBlue = dis.VoteCountBlue
        
    else :
        dis.WastedBlue = (dis.VoteCountBlue - dis.VoteCountRed)/2
        dis.WastedRed = dis.VoteCountRed
    dis.UpdateCMPStats((dis.WastedRed - dis.WastedBlue) / (dis.VoteCountRed+dis.VoteCountBlue))
    if dis.VoteCountRed == dis.VoteCountBlue :
            ran = np.random.randint(2)
            if ran == 0:
                dis.VoteCountRed += 1
            else :
                dis.VoteCountBlue += 1
    dis = DistrictList[dist2-1]
    if dis.VoteCountRed > dis.VoteCountBlue:
        dis.WastedRed = (dis.VoteCountRed - dis.VoteCountBlue)/2
        dis.WastedBlue = dis.VoteCountBlue
    else :
        dis.WastedBlue = (dis.VoteCountBlue - dis.VoteCountRed)/2
        dis.WastedRed = dis.VoteCountRed
    dis.UpdateCMPStats((dis.WastedRed - dis.WastedBlue) / (dis.VoteCountRed+dis.VoteCountBlue))
    if dis.VoteCountRed == dis.VoteCountBlue :
            ran = np.random.randint(2)
            if ran == 0:
                dis.VoteCountRed += 1
            else :
                dis.VoteCountBlue += 1
    return DistrictList
    

def AddNewMapStats(MapList, DistrictList, itCount):
    MapList.append(Map(itCount))
    MapList[-1].UpdateMapStats(DistrictList)
    return MapList

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
    global DistrictList
    global MapList
    global V_Points
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
    arcpy.env.qualifiedFieldNames = False #Needed for AddJoin in ArcPy
    
    try: #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
        shapefile=sys.argv[1]
        zoneField = sys.argv[2]
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
    arcpy.sa.ZonalGeometryAsTable(inZoneData, zoneField, outTable)
    with arcpy.da.SearchCursor(outTable, "*", "*") as cursor:
        for row in cursor:
            DistrictList.append(District(row[1]))
            DistrictList[-1].UpdateStats(row[2], row[3], 4*math.pi*float(row[2])/float(row[3])**2)
    
    MapList = []
    itCount = 0
    MapList.append(Map(itCount))   
    
    with arcpy.da.SearchCursor(path+"\\tl_2020_45_county20_MC1_2018Votes", ["Cluster_ID", "Vote_Blue", "Vote_Red"], "*") as cursor:
        for row in cursor:
            DistrictList[int(row[0]) - 1].VoteCountRed += int(row[2])
            DistrictList[int(row[0]) - 1].VoteCountBlue += int(row[1])
    
    for dis in DistrictList:
        if dis.VoteCountRed == dis.VoteCountBlue :
            ran = np.random.randint(2)
            if ran == 0:
                dis.VoteCountRed += 1
            else :
                dis.VoteCountBlue += 1
        if dis.VoteCountRed > dis.VoteCountBlue:
            dis.WastedRed = (dis.VoteCountRed - dis.VoteCountBlue)/2
            dis.WastedBlue = dis.VoteCountBlue
        else :
            dis.WastedBlue = (dis.VoteCountBlue - dis.VoteCountRed)/2
            dis.WastedRed = dis.VoteCountRed
        dis.UpdateCMPStats((dis.WastedRed - dis.WastedBlue) / (dis.VoteCountRed+dis.VoteCountBlue))

        
    MapList[-1].UpdateMapStats(DistrictList)
    return(MapList)            
        
    return(DistrictList)
    
    
    # To update the DistrictList, call the function:
    ##  PolsbyPopperUpdate(dist1, dist2,shapefile, path, DistrictList,zoneField)
    # To then update the voting counts on this DistrictList, call the function:
    ##  CompetitionUpdate(dist1, dist2, DistrictList)
    # Then to update the total map stats based on these districts call the lines:
    ##  MapList.append(Map(itCount))
    ##  MapList[-1].UpdateMapStats(self, DistrictList)
    
        
if __name__ == "__main__":
    main()