# -*- coding: utf-8 -*-
"""
Created on Fri Jul 23 13:04:43 2021

@author: Blake Splitter and Amy Burton
"""

from __future__ import division
import arcpy,os, sys
#import CreateSpanningTree
import numpy as np
import math
import statistics

#from arcpy.sa import *

class District:
    Area = 0
    Perimeter = 0
    ppCompactScore = 0
    HypArea = 0
    HypPerimeter = 0
    HypppCompactScore = 0
    VoteCountRed = 0
    VoteCountBlue = 0
    WastedRed = 0
    WastedBlue = 0
    BlueShare = 0
    HypVoteCountRed = 0
    HypVoteCountBlue = 0
    HypWastedRed = 0
    HypWastedBlue = 0
    HypBlueShare = 0
    EfficiencyGap = 0  #This will be terms of the dist: wastedRed votes in this district - wastedblue votes in this district, divided by total number of votes
    HypEfficiencyGap = 0
    WinThreshold = 0
    HypWinThreshold = 0
    Original = True
    Population = 0
    
    
    def __init__(self, ID):
        self.ID = ID
    
    def UpdateStats(self, a, p, vcr, vcb, wr, wb, bs, eg, wt):
        self.Area = a
        self.Perimeter = p
        self.ppCompactScore = 4 * math.pi * a / p ** 2  #Polsby-Popper score
        self.VoteCountRed = vcr
        self.VoteCountBlue = vcb
        self.WastedRed = wr
        self.WastedBlue = wb
        self.BlueShare = bs
        self.EfficiencyGap = eg
        self.WinThreshold = wt
    
    def UpdateCompStats(self, a, p, ppc):
        self.Area = a
        self.Perimeter = p
        self.ppCompactScore = ppc
        
    def UpdateHypStats(self, a, p):
        self.HypArea = a
        self.HypPerimeter = p
        self.HypppCompactScore = 4 * math.pi * a / p ** 2  #Polsby-Popper score
        
    
    def ConfirmStats(self, status):
        if status == True:
            self.UpdateStats(self.HypArea, self.HypPerimeter, self.HypVoteCountRed, self.HypVoteCountBlue, self.HypWastedRed, self.HypWastedBlue, self.HypBlueShare, self.HypEfficiencyGap, self.HypWinThreshold)
        self.HypArea = 0
        self.HypPerimeter = 0
        self.HypppCompactScore = 0
        self.HypVoteCountRed = 0
        self.HypVoteCountBlue = 0
        self.HypWastedRed = 0
        self.HypWastedBlue = 0
        self.HypBlueShare = 0
        self.HypEfficiencyGap = 0
        self.HypWinThreshold = 0
            
        
    
class Map:
    ItNum = 0
    WastedVotesRed = 0
    WastedVotesBlue = 0
    TotalRedVotes = 0
    TotalBlueVotes = 0 
    TotalVotes = 0
    EG = 0 
    MedianMean = 0
    B_G = 0
    AvgStateWideVote = 0
    BlueSeatsWon = 0
    HypWastedVotesRed = 0
    HypWastedVotesBlue = 0
    HypTotalRedVotes = 0
    HypTotalBlueVotes = 0 
    HypTotalVotes = 0
    HypEG = 0 
    HypMedianMean = 0
    HypB_G = 0
    HypAvgStateWideVote = 0
    HypBlueSeatsWon = 0
    
    def __init__(self, it):
        self.ItNum = it
    
    def UpdateMapStats(self, wvr, wvb, trv, tbv, tv, eg, mm, bg, aswv, bsw):
        self.WastedVotesRed = wvr
        self.WastedVotesBlue = wvb
        self.TotalRedVotes = trv
        self.TotalBlueVotes = tbv
        self.TotalVotes = tv
        self.EG = eg
        self.MedianMean = mm
        self.B_G = bg
        self.AvgStateWideVote = aswv
        self.BlueSeatsWon = bsw
        self.ItNum += 1
    
    def UpdateHypMapStats(self, DistrictList):
            # Runs through districtList to create AvgppCompactScore and EG and Median_Mean
            Ashares = dict()
            District_Efficiency_Gaps = dict()
            NUM_DISTRICTS = len(DistrictList)
            for i in range(NUM_DISTRICTS):
                dis = DistrictList[i]
                self.HypTotalRedVotes += dis.HypVoteCountRed
                self.HypTotalBlueVotes += dis.HypVoteCountBlue
                self.HypTotalVotes += dis.HypVoteCountRed + dis.HypVoteCountBlue
                self.HypWastedVotesRed += dis.HypWastedRed
                self.HypWastedVotesBlue += dis.HypWastedBlue
                Ashares[i+1] = dis.HypBlueShare
                District_Efficiency_Gaps[i + 1] = dis.HypEfficiencyGap
           # print(Ashares)
            # Average Statewide Vote
            sum_vd = 0
            for d in Ashares.keys():
                sum_vd += Ashares[d]
            V = (1/NUM_DISTRICTS) * sum_vd
            self.HypAvgStateWideVote = V
            # Estimated Seat Proportion
            sum_DEM_seats = 0
            for d in Ashares.keys():
                if Ashares[d] > 0.5:
                    sum_DEM_seats += 1
            SV = (1/NUM_DISTRICTS) * sum_DEM_seats
            self.HypBlueSeatsWon =SV
    
            #print("Average Statewide Vote: V = " + str(V))
            #print("Democratic Seats Won: SV = " + str(sum_DEM_seats) + "/" + str(NUM_DISTRICTS) + " = " + str(SV))
            
            MED = statistics.median(Ashares.values())
            MM = MED-V
            self.HypMedianMean = MM
            #print("MM = " + str(MM))
#            
#            #print(District_Efficiency_Gaps)
#            # Take the average district-wide efficiency gap to see who wastes more votes on average per district
#            EG = statistics.mean(District_Efficiency_Gaps.values())
#            self.HypEG = EG
#            #print(EG)
#            
#            # New Statewide Proportions
#            new_Vs = []
#            new_Vs.append(V)
#            
#            # For each observed proportion of Democratic votes in a district...
#            for d in Ashares.keys():
#                # If a Republican occupies the seat:
#                if Ashares[d] < 0.5:
#                    # The seat will be lost if the statewide vote falls to new_V:
#                    new_V = 1 - (1-V)/(2*(1-Ashares[d]))
#                # If a Democrat occupies the seat:
#                elif Ashares[d] > 0.5:
#                    new_V = V / (2*Ashares[d])
#                else: #if Ashares[d] = 0.5
#                    raise KeyError("District Democratic Vote Proportion exactly equal to 0.5?")
#                
#                new_Vs.append(new_V)
#                
#            MPS_SV = []
#            new_Vs = sorted(new_Vs)
#            for i in range(len(new_Vs)):
#                MPS_SV.append((new_Vs[i],i/(len(new_Vs)-1)))
#                
#            # print MPS_SV
#            
#            MPS_SVI = []
#            for point in MPS_SV:
#                MPS_SVI.append((1-point[0],1-point[1]))
#            MPS_SVI = sorted(MPS_SVI)
#            
#            # print MPS_SVI
#            
#            # Find intersection points.
#            int_pts2 = []
#            for i in range(len(MPS_SV)-1):
#                # If we find where two line segments intersect...
#                if (MPS_SV[i][0] < MPS_SVI[i][0] and MPS_SV[i+1][0] > MPS_SVI[i+1][0]) or (MPS_SV[i][0] > MPS_SVI[i][0] and MPS_SV[i+1][0] < MPS_SVI[i+1][0]):
#                    # Find Seats-Votes line segment.
#                    m1 = (MPS_SV[i+1][1]-MPS_SV[i][1]) / (MPS_SV[i+1][0]-MPS_SV[i][0])
#                    b1 = MPS_SV[i][1] - m1 * MPS_SV[i][0]
#                    
#                    # Find Inverted Seats-Votes line segment.
#                    m2 = (MPS_SVI[i+1][1]-MPS_SVI[i][1]) / (MPS_SVI[i+1][0]-MPS_SVI[i][0])
#                    b2 = MPS_SVI[i][1] - m2 * MPS_SVI[i][0]
#                    
#                    # Find the intersection point.
#                    x = (b2-b1)/(m1-m2)
#                    y = m1 * x + b1
#                    
#                    int_pts2.append((x,y))
#                    
#            # print int_pts2
#            
#            # Append intersection points to SV and SVI points, then sort.
#            for pt in int_pts2:
#                MPS_SV.append(pt)
#                MPS_SVI.append(pt)
#            MPS_SV = sorted(MPS_SV)
#            MPS_SVI = sorted(MPS_SVI)
#            
#            # Calculate total area under the SV and Inverse SV curves.
#            BG_MPS = 0
#            
#            # 'Integrate' with respect to y
#            xmax2 = max(MPS_SV[-1][0], MPS_SVI[-1][0])
#            
#            for i in range(len(MPS_SV)-1):
#                # Area under Seats-Votes curve
#                b1 = xmax2 - MPS_SV[i][0]
#                b2 = xmax2 - MPS_SV[i+1][0]
#                h = MPS_SV[i+1][1] - MPS_SV[i][1]
#                area1 = 0.5 * (b1 + b2) * h
#                
#                # Area under Inverted Seats-Votes curve
#                ib1 = xmax2 - MPS_SVI[i][0]
#                ib2 = xmax2 - MPS_SVI[i+1][0]
#                ih = MPS_SVI[i+1][1] - MPS_SVI[i][1]
#                area2 = 0.5 * (ib1 + ib2) * ih
#                
#                BG_MPS += abs(area2 - area1)
#                
#            self.HypB_G = BG_MPS            
#            #print("Under the MPS assumption, B_G = " + str(BG_MPS) + " or " + str(round(BG_MPS*100,2)) + "%")
            
    def ConfirmMapStats(self, status):
        if status == True:
            self.UpdateMapStats(self.HypWastedVotesRed, self.HypWastedVotesBlue, self.HypTotalRedVotes, self.HypTotalBlueVotes, self.HypTotalVotes, self.HypEG, self.HypMedianMean, self.HypB_G, self.HypAvgStateWideVote, self.HypBlueSeatsWon)
        self.HypWastedVotesRed = 0
        self.HypWastedVotesBlue = 0
        self.HypTotalRedVotes = 0
        self.HypTotalBlueVotes = 0 
        self.HypTotalVotes = 0
        self.HypEG = 0 
        self.HypMedianMean = 0
        self.HypB_G = 0
        self.HypAvgStateWideVote = 0
        self.HypBlueSeatsWon = 0
        
def DistrictUpdateForHyp(dist1, dist2, shapefile, path, DistrictList, voteBlueField, voteRedField):
    #Create a Reduced Shapefile just based on dist1 and dist2, and update the appropriate districts in DistrictList
    inZoneData = shapefile
    zoneField = "temp_dist"
    outTable = path + "\\TempDistrictZonalGeometry"
    #cellSize = 1.28781240014216E-02
    arcpy.CheckOutExtension("Spatial")
    arcpy.sa.ZonalGeometryAsTable(inZoneData, zoneField, outTable)
    with arcpy.da.SearchCursor(outTable, "*", '''{}={} OR {}={}'''.format("Value", 1, "Value", 2)) as cursor:
        for row in cursor: 
            if row[1] == 1:  #If the district is temp_dist1
                DistrictList[dist1-1].UpdateHypStats(row[2], row[3])
            elif row[1] == 2:  #If the district is temp_dist2
                DistrictList[dist2-1].UpdateHypStats(row[2], row[3])
    for i in range(len(DistrictList)):
        if i != dist1 - 1 and i != dist2 - 1:
            DistrictList[i].UpdateHypStats(DistrictList[i].Area, DistrictList[i].Perimeter)
    #return DistrictList

    #DistrictList[dist1 - 1].HypVoteCountRed = 0
    #DistrictList[dist1 - 1].HypVoteCountBlue = 0
    #DistrictList[dist2 - 1].HypVoteCountRed = 0
    #DistrictList[dist2 - 1].HypVoteCountBlue = 0
    with arcpy.da.SearchCursor(shapefile, ["SOURCE_ID", "temp_dist", voteRedField, voteBlueField], '''{}={} OR {}={}'''.format("temp_dist",1,"temp_dist",2)) as cursor:
        for row in cursor:
            if row[1]==1:
                DistrictList[dist1-1].HypVoteCountRed += row[2]
                DistrictList[dist1-1].HypVoteCountBlue += row[3]
            if row[2]==2:
                DistrictList[dist1-1].HypVoteCountRed += row[2]
                DistrictList[dist1-1].HypVoteCountBlue += row[3]

    dis = DistrictList[dist1-1]
    if dis.HypVoteCountRed == dis.HypVoteCountBlue :
        ran = np.random.randint(2)
        if ran == 0:
            dis.HypVoteCountRed += 1
        else :
            dis.HypVoteCountBlue += 1
    #Calculate win threshold:
    if dis.HypVoteCountRed + dis.HypVoteCountBlue % 2 == 0:
        dis.HypWinThreshold = (0.5 * (dis.HypVoteCountRed + dis.HypVoteCountBlue)) + 1
    else :
        dis.HypWinThreshold = math.ceil(0.5 * (dis.HypVoteCountRed + dis.HypVoteCountBlue))
    if dis.HypVoteCountRed > dis.HypVoteCountBlue:
        dis.HypWastedRed = dis.HypVoteCountRed - dis.HypWinThreshold
        dis.HypWastedBlue = dis.HypVoteCountBlue
    else :
        dis.HypWastedBlue = dis.HypVoteCountBlue - dis.HypWinThreshold
        dis.HypWastedRed = dis.HypVoteCountRed
    dis.HypBlueShare = dis.HypVoteCountBlue / (dis.HypVoteCountRed + dis.HypVoteCountBlue)
    dis.HypEfficiencyGap = (dis.WastedBlue - dis.WastedRed) / (dis.VoteCountRed + dis.VoteCountBlue)
    
    dis = DistrictList[dist2 - 1]
    if dis.HypVoteCountRed == dis.HypVoteCountBlue :
        ran = np.random.randint(2)
        if ran == 0:
            dis.HypVoteCountRed += 1
        else :
            dis.HypVoteCountBlue += 1
    #Calculate win threshold:
    if dis.HypVoteCountRed + dis.HypVoteCountBlue % 2 == 0:
        dis.HypWinThreshold = (0.5*(dis.HypVoteCountRed + dis.HypVoteCountBlue)) + 1
    else :
        dis.HypWinThreshold = math.ceil(0.5*(dis.HypVoteCountRed + dis.HypVoteCountBlue))
    if dis.HypVoteCountRed > dis.HypVoteCountBlue:
        dis.HypWastedRed = dis.HypVoteCountRed - dis.HypWinThreshold
        dis.HypWastedBlue = dis.HypVoteCountBlue
    else :
        dis.HypWastedBlue = dis.HypVoteCountBlue - dis.HypWinThreshold
        dis.HypWastedRed = dis.HypVoteCountRed
    dis.HypBlueShare = dis.HypVoteCountBlue / (dis.HypVoteCountRed + dis.HypVoteCountBlue)
    dis.HypEfficiencyGap = (dis.WastedBlue - dis.WastedRed)/(dis.VoteCountRed + dis.VoteCountBlue)
            
    return DistrictList.copy()
    

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
        
def main(*args):
    ### MAIN CODE STARTS HERE
    global DistrictList
    global MapObject
    global runspot  #Allows runspot to be changed inside a function
    global voteRedField
    global voteBlueField
    
    if sys.executable == r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe": #Change this line if ArcGIS is located elsewhere
        runspot = "ArcGIS"
        if __name__ == "__main__":
            arcprint("We are running GraphMeasures.py from inside ArcGIS")
    else:
        runspot = "console"
        if __name__ == "__main__":
            arcprint("We are running GraphMeasures.py from the python console")
    
    currentdir = os.getcwd()
    path = currentdir + "\\SC_Redistricting_Updated.gdb"
    arcpy.env.workspace = path
    arcpy.env.overwriteOutput=True
    arcpy.env.qualifiedFieldNames = False #Needed for AddJoin in Arcpy
    
    try: #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
        shapefile = sys.argv[1]
        zoneField = sys.argv[2]
        voteBlueField = sys.argv[3]
        voteRedField = sys.argv[4]
    except IndexError: 
        try: #Second, tries to take input from explicit input into main()
            shapefile = args[0]
            zoneField = args[1]
            voteBlueField = args[2]
            voteRedField = args[3]
        except IndexError: #Finally, manually assigns input values if they aren't provided
            shapefile = path + "\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1"
            zoneField = "Cluster_ID"
            voteBlueField = "PresBlue"
            voteRedField = "PresRed"
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
            DistrictList[-1].UpdateHypStats(row[2], row[3])
    

    MapObject = Map(0)  
    
    with arcpy.da.SearchCursor(shapefile, ["Dist_Assign", voteBlueField, voteRedField], "*") as cursor:
        for row in cursor:
            try: 
                DistrictList[int(row[0]) - 1].HypVoteCountRed += int(row[2])
                DistrictList[int(row[0]) - 1].HypVoteCountBlue += int(row[1])
            except TypeError:
                DistrictList[int(row[0]) - 1].HypVoteCountRed += 0
                DistrictList[int(row[0]) - 1].HypVoteCountBlue += 0
    
    for dis in DistrictList:
        if dis.HypVoteCountRed == dis.HypVoteCountBlue:
            ran = np.random.randint(2)
            if ran == 0:
                dis.HypVoteCountRed += 1
            else :
                dis.HypVoteCountBlue += 1
        #Calculate win threshold:
        if dis.HypVoteCountRed + dis.HypVoteCountBlue % 2 == 0:
            dis.HypWinThreshold = (0.5*(dis.HypVoteCountRed + dis.HypVoteCountBlue)) + 1
        else :
            dis.HypWinThreshold = math.ceil(0.5*(dis.HypVoteCountRed + dis.HypVoteCountBlue))
        if dis.HypVoteCountRed > dis.HypVoteCountBlue:
            dis.HypWastedRed = dis.HypVoteCountRed - dis.HypWinThreshold
            dis.HypWastedBlue = dis.HypVoteCountBlue
        else :
            dis.HypWastedBlue = dis.HypVoteCountBlue - dis.HypWinThreshold
            dis.HypWastedRed = dis.HypVoteCountRed
        dis.HypBlueShare = dis.HypVoteCountBlue / (dis.HypVoteCountRed + dis.HypVoteCountBlue)
        dis.HypEfficiencyGap = (dis.HypWastedBlue - dis.HypWastedRed)/(dis.HypVoteCountRed + dis.HypVoteCountBlue)
        
        
    MapObject.UpdateHypMapStats(DistrictList)
    for i in range(len(DistrictList)):
        DistrictList[i].ConfirmStats(True)
    MapObject.ConfirmMapStats(True)
    #return(DistrictList)
    

    return(DistrictList.copy(), MapObject)    
    
   # To update DistrictList with hypothetical information:
   ## GraphMeasures.DistrictUpdateForHyp(dist1, dist2,shapefile, path, DistrictList)
   # To update the hypothetical Map List based on these numbers:
   ## MapObject.UpdateHypMapStats(DistrictList)
   # To confirm(or reject ) the updates:
   ## DistrictStats[dist1-1].ConfirmStats(True)
   ## DistrictStats[dist2-1].ConfirmStats(True)
   ## MapObject.ConfirmMapStats(True)
   
    
        
if __name__ == "__main__":
    main()