# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 16:52:28 2021

@author: Blake Splitter
"""
### IMPORTANT ASSUMPTION: WE ASSUME THAT THE FIRST COLUMN OF THE FEATURE LAYER
### IS AN ID COLUMN THAT UNIQUELY LABELS EACH ROW WITH THE NUMBERS 1-X, WHERE
### X IS THE NUMBER OF ROWS

#TO DO LIST
"#1. Change argv stuff --- DONE (Blake)"
#2. Consider new starting temperatures and whatnot
"#3. Use build-balanced-zones --- DONE (Blake)"
"#4. Figure out what to do with x --- DONE. Essentially deleted. (Blake)"
"#5. Need to update boundary list with each pass through the code --- DONE (Blake)"
#6. Need to measure initial energy
#7. Need to generalize odn stuff
#8. Consider adjusting smallest possible temperature
#9. Determine how to add a map to the contents pane if and only if it is not already there.
#10. Make this code create its own neighbor list
#11. Consider appending population field and custom naming field to out_table
#12. Add timers to time sections of code
#13. Reconsider starting temperatures
#14. Make code modular enough to change input metrics

import arcpy,math,os,sys
import random
seed = 1743
random.seed(seed)
import CreateSpanningTree
import CreateNeighborList
import networkx as nx
import GraphMeasures
import County_Intersections
import numpy as np
import datetime


def Flip():
    '''THE FOLLOWING CODE IS ESSENTIALLY THE FLIP ALGORITHM
        
        
        randshape = 45000
        adder = random.randint(0,45)
        randshape = randshape + adder*2+1
        #This cursor line updates one preinct at a time. 
        with arcpy.da.UpdateCursor(out_table, [NameField, DistField, PopField],"""{0}='{1}'""".format(NameField,randshape)) as cursor:
        #with arcpy.da.UpdateCursor(out_table, [NameField, DistField, PopField],"GEOID20 = '27'") as cursor:
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
        DeltaE_dev = deviation[count] - deviation[count-1]
        arcprint("DeltaE_dev = {0}. T = {1}",DeltaE_dev,T)
        if DeltaE_dev <0:
            T = T*.997
            continue
        else :
            rand = random.uniform(0,1)
            try: 
                p = 1/math.exp(DeltaE_dev/T)
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
                with arcpy.da.UpdateCursor(out_table, [NameField, DistField, PopField],"{0} = '{1}'".format(NameField,randshape)) as cursor:
                    for row in cursor:
                        row[1] = currdist
                        cursor.updateRow(row)''' 

def DeviationFromIdealPop(sumpop,idealpop,distcount):
    """Returns a single positive integer that sums each district's deviation from the ideal population. Lower numbers for 'deviation' are better. A value of zero would indicate that every district has an equal number of people"""
    absdev = [0 for i in range(distcount)]
    
    for i in range(distcount):
        absdev[i] = abs(sumpop[i]-idealpop)
    deviation_ = sum(absdev)
    deviation_ = round(deviation_)
    return(deviation_)
    
#%%
    
def acceptchange(T,hypsumpop,hypstateG,hypG,dist1,dist2,nlf,neighbor_list,out_table,DistField,DistrictStats,MapStats, units_in_CDI, temp_units_in_CDI, geo_unit_list):
    T=T*coolingrate
    sumpop = hypsumpop.copy()
    stateG = hypstateG.copy()
    arcprint("The change was accepted!")
    
    #Updates the neighbor list table after each iteration
    #Note: nlf[3] = 'src_dist', nlf[4] = 'nbr_dist'
    with arcpy.da.UpdateCursor(neighbor_list,nlf,'''{}={} OR {}={} OR {}={} OR {}={}'''.format(nlf[3], dist1, nlf[4], dist1, nlf[3], dist2, nlf[4], dist2)) as cursor:
        for row in cursor:
            if row[0] in hypG.nodes:
                row[3] = hypG.nodes[row[0]]["District Number"]
            if row[1] in hypG.nodes:
                row[4] = hypG.nodes[row[1]]["District Number"]
            cursor.updateRow(row)
        del cursor
        del row
    
    #Updates the shapefile with current district numbers
    with arcpy.da.UpdateCursor(out_table,["SOURCE_ID",DistField], '''{}={} OR {}={}'''.format(DistField,dist1,DistField,dist2)) as cursor:
        for row in cursor:
            objid= row[0]
            row[1] = stateG.nodes[objid]["District Number"]
            cursor.updateRow(row)
    geo_unit_list[dist1-1] = []
    geo_unit_list[dist2-1] = []
    with arcpy.da.SearchCursor(out_table,["SOURCE_ID", DistField], '''{}={} OR {}={}'''.format(DistField,dist1,DistField,dist2)) as cursor:
        for row in cursor:
            if row[1] == dist1:
                geo_unit_list[dist1-1].append(row[0])
            elif row[1] == dist2:
                geo_unit_list[dist2-1].append(row[0])
            else :
                arcprint("WE HAVE AN ERROR!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    geo_unit_list[dist1-1].sort()
    geo_unit_list[dist2-1].sort()
    DistrictStats[dist1-1].ConfirmStats(True)
    DistrictStats[dist2-1].ConfirmStats(True)
    MapStats.ConfirmMapStats(True)
    
    units_in_CDI[dist1-1] = temp_units_in_CDI[0]
    units_in_CDI[dist2-1] = temp_units_in_CDI[1]
    
    temp_units_in_CDI = np.zeros([2,46], dtype=int)
    
    arcprint("Total number of precincts = {0} (calculated by np.sum(units_in_CDI, inside acceptchange, line 177)", np.sum(units_in_CDI))
       
    #arcprint("The fairness scores for this map are: Median_Mean = {0}", MapStats.MedianMean)
    arcprint("CDI_Count = {0}", np.count_nonzero(units_in_CDI))
    
    #return(T,sumpop,stateG,neighbor_list,DistrictStats)
    return(T,sumpop,stateG,neighbor_list,DistrictStats,MapStats, units_in_CDI, geo_unit_list)
        
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

#%% START MAIN CODE
def main(*args):
    global runspot #Allows runspot to be changed inside a function
    
    if sys.executable == r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe": #Change this line if ArcGIS is located elsewhere
        runspot = "ArcGIS"
    else:
        runspot = "console"
            
    # Set environment settings
    global currentdir
    global path
    
    currentdir = os.getcwd()
    path = currentdir + "\\SC_Redistricting_Updated.gdb"
    arcpy.env.workspace = path
    
    arcpy.env.overwriteOutput = True
    
    global coolingrate
    
    try: #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
        in_table = sys.argv[1]
        in_pop_field = sys.argv[2]
        in_name_field = sys.argv[3]
        distcount = int(sys.argv[4])
        MaxIter = int(sys.argv[5])
        T = float(sys.argv[6])
        FinalT = float(sys.argv[7])
        coolingrate = (FinalT/T)**(1/MaxIter)
        tol = float(sys.argv[8])
        maxstopcounter = sys.argv[9]
    except IndexError: 
        try: #Second, tries to take input from explicit input into main()
            in_table = args[0]
            in_pop_field = args[1]
            in_name_field = args[2]
            distcount = int(args[3])
            MaxIter = int(args[4])
            T = float(args[5])
            FinalT = float(args[6])
            coolingrate = (FinalT/T)**(1/MaxIter)
            tol = float(args[7])
            maxstopcounter = args[8]
        except IndexError: #Finally, manually assigns input values if they aren't provided
#            in_table=path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1"
#            in_pop_field = "SUM_Popula"
#            in_name_field = "OBJECTID"
            in_table = path + "\\Precincts_2020"
            in_pop_field = "Precinct_P"
            in_name_field = "OBJECTID_1"
            distcount=7
            MaxIter=50
            T = 20
            FinalT = 0.1
            coolingrate = (FinalT/T)**(1/MaxIter)
            tol=30
            maxstopcounter=100
            arcprint("We are using default input choices")
    
    #Marking the start time of the run.
    now = datetime.datetime.now()
    arcprint("Starting date and time : {0}",now.strftime("%Y-%m-%d %H:%M:%S"))
    
    #This builds alpha, which is the normalized unit vector that details how much we care about any given metric. 
    metric_count = 5
    alpha = metric_count*[0]
#    for i in range(metric_count):
#        alpha[i] = random.randint(1,1000)
#    tot = sum(alpha)
#    for i in range(metric_count):
#        alpha[i] = alpha[i]/tot
    alpha = [0.7, 0.15, 0, 0.075, 0.075]
    arcprint("alpha = {0}",alpha)
        
    #Normalizing factor
    prev_DeltaE = np.zeros([5,metric_count],dtype=float)
    norm = [0]*metric_count
    
    #Counts number of rows in out_table      
    row_count = arcpy.GetCount_management(in_table).getOutput(0) #getOutput(0) returns the value at the first index position of a tool.
    row_count=int(row_count)
    
    #MIGHT WANT TO MAKE OUT_TABLE HAVE A UNIQUE NAME
    #out_table = in_table + "_SA_" + "{0}".format(distcount) + "dists"
    out_table = in_table + "_SA_" + "{0}".format(distcount) + "dists" 
    #out_table = arcpy.CreateUniqueName(in_table + "_SA")

    #Using Spatially Constrained Multivariate Clustering instead of BBZ to create a random starting district
    if not arcpy.ListFields(in_table, "Test_val"): #if field does not exist
        arcpy.AddField_management(in_table, "Test_val","LONG",field_alias="Test_val")
        arcprint("Adding 'Test_val' field to in_table")
    with arcpy.da.UpdateCursor(in_table, 'Test_val') as cursor:
        for row in cursor:
            row[0] = random.randint(1,100000)
            cursor.updateRow(row)
    arcprint("Running Spatially Constrained Multivariate Clustering...")
    arcpy.stats.SpatiallyConstrainedMultivariateClustering(in_table,out_table, "Test_val",size_constraints="NUM_FEATURES", min_constraint=0.65*row_count/distcount,  number_of_clusters=distcount, spatial_constraints="CONTIGUITY_EDGES_ONLY")
    
    #Adds populations as a column in out_table
    arcpy.management.JoinField(out_table, "SOURCE_ID", in_table, in_name_field, in_pop_field)
    
    #Adds vote totals as a column in out_table
    arcpy.management.JoinField(out_table, "SOURCE_ID", in_table, in_name_field, "Vote_Blue")
    arcpy.management.JoinField(out_table, "SOURCE_ID", in_table, in_name_field, "Vote_Red")
    
    #Adds county numbers to out_table
    arcpy.management.JoinField(out_table, "SOURCE_ID", in_table, in_name_field, "County")
    
    #Creates a column named "temp_dist" and zeros it out
    if not arcpy.ListFields(out_table, "temp_dist"):
        arcpy.AddField_management(out_table, "temp_dist", "SHORT", field_alias="Temporary District")
    with arcpy.da.UpdateCursor(out_table, "temp_dist") as cursor:
        for row in cursor: 
            row[0] = 0
            cursor.updateRow(row)
    
    #Assigns DistField as "Dist_Assgn" and creates the field if it's not already there
    if not arcpy.ListFields(out_table, "Dist_Assgn"):
        arcpy.AddField_management(out_table, "Dist_Assgn", "SHORT", field_alias="DIST_ASSIGNMENT")
    DistField="Dist_Assgn"

    #Runs CreateNeighborList and returns the name of the neighbor_list
    neighbor_list = CreateNeighborList.main(out_table)

    arcpy.AddField_management(out_table, "County_Num", "SHORT", field_alias="County_Num")
    CountyField = "County_Num"
    geo_unit_list = [[ ] for d in range(distcount)]
    arcprint(geo_unit_list)
    # Copies all CLUSTER_ID's into Dist_Assgn
    with arcpy.da.UpdateCursor(out_table, [DistField,"CLUSTER_ID", "SOURCE_ID","County","County_Num"]) as cursor:
        for row in cursor:
            row[0] = row[1] #Dist_Assgn = CLUSTER_ID
            row[4] = int(row[3]) #County_Num = County
            geo_unit_list[row[0]-1].append(row[2])
            cursor.updateRow(row)
    ucount = 0
    for unit in geo_unit_list:
        ucount += 1
        unit.sort()
        arcprint("At the start, the total number of geographic units in District{0} is {1}.", ucount, len(unit))
    
    #Finds sum of each district population
    sumpop=[]
    sumpop = [0]*distcount
    with arcpy.da.SearchCursor(out_table, [in_pop_field,DistField]) as cursor:
        for row in cursor:
            #i = district number minus 1, since district numbers range from 1 to distcount
            i = row[1]-1
            i = int(i)
            sumpop[i] = row[0] + sumpop[i]
    idealpop=sum(sumpop)/distcount
    arcprint("The sum of unit populations (i.e. sumpop) is {0}. Thus, the ideal population for a district is {1}.",sumpop,idealpop)
    
    [DistrictStats, MapStats] = GraphMeasures.main(out_table, DistField) #Populates DistrictStats and MapStats using GraphMeasures
    comp = [o.ppCompactScore for o in DistrictStats]    #comp is a list of compactness scores
    fair = MapStats.MedianMean     #fair is a list of MedianMean scores
    
    #Populates County-District-Intersection (CDI) values
    [units_in_CDI, CDI_Count, CDI_Square] = County_Intersections.main(out_table,distcount,DistField)
    temp_units_in_CDI = np.zeros([2,46], dtype=int)
    
    arcprint("The fairness scores for this map are: Median_Mean = {0}", fair)
    arcprint("CDI_Count = {0}", CDI_Count)
    arcprint("Total number of precincts (calculated by np.sum(units_in_CDI)) = {0}", np.sum(units_in_CDI))
    arcprint("CDI_Square = {0}", CDI_Square)
    
    #Creates vectors of zeros that will hold values for population deviation, average compactness, etc.
    deviation =[0]*(MaxIter+1)
    avgcomp = [0]*(MaxIter+1)  
    fairscore = [0]*(MaxIter+1)
    r_fairscore = [0]*(MaxIter+1)
    CDI_Count_vals = [0]*(MaxIter+1)
    CDI_Square_vals = [0]*(MaxIter+1)
    
    #Populates the zeroth entry for all vectors
    deviation[0] = DeviationFromIdealPop(sumpop, idealpop, distcount)
    avgcomp[0] = sum(comp)/len(comp)
    fairscore[0] = abs(fair)
    r_fairscore[0] = fair
    CDI_Count_vals[0] = CDI_Count
    CDI_Square_vals[0] = CDI_Square
    
    #Initializes neighbor_list so that each entry in src_dist and nbr_dist is reset to match original districts
    if not arcpy.ListFields(neighbor_list, "src_dist"): #Adds src_dist and nbr_dist to neighbor_list if they don't already exist. These fields will be the ones that change mid-algorithm
        arcpy.AddField_management(neighbor_list, "src_dist", "SHORT", field_alias="Source District")
        arcpy.AddField_management(neighbor_list, "nbr_dist", "SHORT", field_alias="Neighbor District")
    orig_dist_names=[]
    lstFields = arcpy.ListFields(neighbor_list)
    for field in lstFields:
        if field.name in ["src_CLUSTER_ID", "src_ZONE_ID", "nbr_CLUSTER_ID", "nbr_ZONE_ID"]:
            orig_dist_names.append(field.name)
    odn=orig_dist_names #An alias
    
    #Copies all original district numbers into src_dist and nbr_dist
    #Note: odn[0] = "src_CLUSTER_ID" and odn[1] = "nbr_CLUSTER_ID"
    with arcpy.da.UpdateCursor(neighbor_list, [odn[0],odn[1],'src_dist', 'nbr_dist']) as cursor:
        for row in cursor:
            row[2]=row[0] #src_dist = src_CLUSTER_ID
            row[3]=row[1] #nbr_dist = nrb_CLUSTER_ID
            cursor.updateRow(row)
    
    hypsumpop=sumpop.copy()
    stateG = nx.Graph()
    
    #Starting the main line of the Simulated Annealing Algorithm
    count = 0 #The number of iterations in which a change was made
    stopcounter=0 #The number of consecutive iterations in which a change was NOT made
    
    while T>0.1 and count<MaxIter and stopcounter<maxstopcounter:
        arcprint("\ncount = {0}. About to add 1.",count)
        count = count+1
        dist1 = random.randint(1,distcount)
        dist2 = random.randint(1,distcount)
        while dist1==dist2: #Randomly selects two different districts
            dist1 = random.randint(1,distcount)
            dist2 = random.randint(1,distcount)
        arcprint("dist1 = {0} and dist2 = {1}.", dist1,dist2)
        try:
            [dist1_pop, dist2_pop, hypstateG, hypG, nlf, prevdists,neighbor_list] = CreateSpanningTree.main(out_table, in_pop_field, "SOURCE_ID", tol, neighbor_list, dist1, dist2, stateG, geo_unit_list)
        except RuntimeError: #Cuts the code if we encounter a Runtime error in CreateSpanningTree
            arcprint("We had a runtime error. Selecting new districts")
            count -= 1
            stopcounter += 1
            continue
        except SystemError: #Cuts the code if we encounter a SystemError in CreateSpanningTree
            arcprint("We had a system error. Selecting new districts")
            count -= 1
            stopcounter += 0 #We don't want non-adjacent district choices to contribute to stopcounter
            continue
        if dist1_pop==float('inf') or dist2_pop==float('inf'):
            count-=1
            stopcounter+=1
            continue
        
#        NotGonnaMove = 0
#        TempDist1 = 0
#        TempDist2 = 0
#        ERRORS = 0
#        with arcpy.da.SearchCursor(out_table, ['temp_dist']) as cursor:
#            for row in cursor:
#                if row[0] == 0:
#                   NotGonnaMove += 1
#                elif row[0] == 1:
#                    TempDist1 += 1
#                elif row[0] == 2:
#                    TempDist2 += 1
#                else :
#                    ERRORS += 1
#                    arcprint("SOMETHING IS WRONG!")
#        arcprint("Number of precincts in: TempDist1 = {0}, TempDist2 = {1}, NotGonnaMove = {2}, So the total number of precincts is: {3}", TempDist1, TempDist2, NotGonnaMove,  TempDist1 +TempDist2 + NotGonnaMove)
            
        #Populates entries of hypothetical population sum (hypsumpop) with the proposed dist1 and dist2 populations
        hypsumpop[dist1-1] = dist1_pop
        hypsumpop[dist2-1] = dist2_pop
        deviation[count] = DeviationFromIdealPop(hypsumpop,idealpop,distcount) #Calculates the absolute deviation from ideal for this proposed change. 
        
        DistrictStats = GraphMeasures.DistrictUpdateForHyp(dist1,dist2, out_table,path, DistrictStats)
        hypcomp = [o.HypppCompactScore for o in DistrictStats] #A list of hypothetical compactness scores
        avgcomp[count] = sum(hypcomp)/len(hypcomp)
        
        MapStats.UpdateHypMapStats(DistrictStats)
        fairscore[count] = abs(MapStats.HypMedianMean)
        r_fairscore[count] = MapStats.HypMedianMean
        
        #CDI_Count_vals[count] = CDI_Count
        [CDI_Count, temp_units_in_CDI, CDI_Square] = County_Intersections.CountIntersections(dist1, dist2, CDI_Count_vals[count-1], units_in_CDI, out_table, "temp_dist", CDI_Square_vals[count-1], CountyField)
        CDI_Count_vals[count] = CDI_Count
        CDI_Square_vals[count] = CDI_Square
        arcprint("Total number of precincts = {0} (should not have changed) line 521", np.sum(units_in_CDI))
           
        DeltaE_dev = deviation[count] - deviation[count-1]
        DeltaE_comp = avgcomp[count-1] - avgcomp[count]
        DeltaE_fair = fairscore[count] - fairscore[count-1]
        DeltaE_county = CDI_Count_vals[count] - CDI_Count_vals[count-1]
        DeltaE_square = CDI_Square_vals[count-1] - CDI_Square_vals[count]
        arcprint("DeltaE_dev = {0}.",DeltaE_dev)
        arcprint("DeltaE_comp = {0}.",DeltaE_comp)
        arcprint("DeltaE_fair = {0}.", DeltaE_fair)
        arcprint("DeltaE_county = {0}.", DeltaE_county)
        arcprint("DeltaE_square = {0}.", DeltaE_square)
        
        prev_DeltaE[count % 5][0] = abs(DeltaE_dev)
        prev_DeltaE[count % 5][1] = abs(DeltaE_comp)
        prev_DeltaE[count % 5][2] = abs(DeltaE_fair)
        prev_DeltaE[count % 5][3] = abs(DeltaE_county)
        prev_DeltaE[count % 5][4] = abs(DeltaE_square)
        for i in range(metric_count):
            norm[i] = sum(prev_DeltaE[:,i])/len(prev_DeltaE[:,i])
            if norm[i] == 0:
                norm[i]=1
        #Calculates DeltaE based on each of the metrics_
        DeltaE = DeltaE_dev*alpha[0]/norm[0]+ DeltaE_comp*alpha[1]/norm[1] + DeltaE_fair*alpha[2]/norm[2] + DeltaE_county*alpha[3]/norm[3] + DeltaE_square*alpha[4]/norm[4]
        arcprint("DeltaE = {0}. T = {1}.",DeltaE,T)
        
        
        if DeltaE <0: #An improvement!
            [T,sumpop,stateG,neighbor_list,DistrictStats, MapStats, units_in_CDI, geo_unit_list] = acceptchange(T,hypsumpop,hypstateG,hypG,dist1,dist2,nlf,neighbor_list,out_table,DistField,DistrictStats,MapStats, units_in_CDI, temp_units_in_CDI, geo_unit_list)
            stopcounter=0
            continue
        else : #A worsening :(
            rand = random.uniform(0,1)
            try: 
                p = 1/math.exp(DeltaE/T) #p = probability that the worsening is accepted
            except OverflowError:
                p = 0 #If denominator in calculation above is large enough, an OverflowError will occur
            if math.isnan(p):
                arcerror("p was nan")
            arcprint("p = {0}. rand = {1}",p,rand)
            if rand<=p: #Worsening is accepted
                #[T,sumpop,stateG,neighbor_list,DistrictsStats] = acceptchange(T,hypsumpop,hypstateG,hypG,dist1,dist2,nlf,neighbor_list,out_table,DistField,DistrictStats)
                [T,sumpop,stateG,neighbor_list,DistrictsStats,MapStats, units_in_CDI,geo_unit_list] = acceptchange(T,hypsumpop,hypstateG,hypG,dist1,dist2,nlf,neighbor_list,out_table,DistField,DistrictStats,MapStats, units_in_CDI, temp_units_in_CDI,geo_unit_list)
                stopcounter=0 #resets the stopcounter
                continue
            else: #undoes the district changes previously made. 
                count = count-1
                nx.set_node_attributes(stateG,prevdists,"District Number")
                stopcounter+=1
                arcprint("The change was rejected, since p < rand.")
                DistrictStats[dist1-1].ConfirmStats(False)
                DistrictStats[dist2-1].ConfirmStats(False)
                MapStats.ConfirmMapStats(False)
                temp_units_in_CDI = np.zeros([2,46], dtype=int)
                
                
        
    arcprint("\n")
    if T<=0.01:
        arcprint("\nSmallest legal temperature reached T = {0}.", T)
    if count >=MaxIter:
        arcprint("\nMaximum number of iterations reached. count = {0} and MaxIter = {1}", count, MaxIter)
    if stopcounter ==maxstopcounter:
        arcprint("\nWe failed in {0} consecutive ReCom attempts, so we will stop here.",maxstopcounter)
    arcprint("Original population deviation from ideal = {0}. Final population deviation = {1}",deviation[0],deviation[count])
    arcprint("Original Polsby Popper Compactness = {0}. Final Compactness = {1}",avgcomp[0],avgcomp[count])
    arcprint("Original Median_Mean Score = {0}. Final Median_Mean Score = {1}",r_fairscore[0],r_fairscore[count])
    arcprint("Original CDI_Count Score = {0}. Final CDI_Count Score = {1}",CDI_Count_vals[0],CDI_Count_vals[count])
    arcprint("Original CDI_Square Score = {0}. Final CDI_Square Score = {1}",CDI_Square_vals[0],CDI_Square_vals[count])
    arcprint("The population of each district is {0}",sumpop)
    arcprint("The compactness of each district is {0}",[o.ppCompactScore for o in DistrictStats])
    arcprint("The relative value assigned to the metrics was: Pop: {0}, Compactness: {1}, MM: {2}, Counties: {3}", alpha[0],alpha[1],alpha[2],alpha[3])
    
    #Repopulates stateG if it was emptied during a rejection step in the algorithm
    distnum = {} #Initializes a dictionary that will contain the district number for each polygon
    popnum = {} #Initializes a dictionary that will contain the population for each polygon
    if nx.is_empty(stateG)==True:
        with arcpy.da.SearchCursor(out_table,["SOURCE_ID",in_pop_field]) as cursor:
            for row in cursor:
                popnum[row[0]] = row[1] #Finds population of each polygon
                stateG.add_node(row[0]) #Adds each polygon to the node list for stateG
        with arcpy.da.SearchCursor(neighbor_list,nlf) as cursor:
            for row in cursor:
                cursor.reset
                if list(stateG.edges).count([row[0],row[1]])==0 and list(stateG.edges).count([row[1],row[0]])==0:
                    stateG.add_edge(row[0],row[1])
                distnum[row[0]]=row[3] #distnum[src_OBJECTID] = src_dist
        nx.set_node_attributes(stateG,popnum,"Population")
        nx.set_node_attributes(stateG,distnum,"District Number")
    
    #Updates the shapefile with current district numbers
    with arcpy.da.UpdateCursor(out_table,["SOURCE_ID","Dist_Assgn"]) as cursor:
        for row in cursor:
            objid= row[0]
            row[1] = stateG.nodes[objid]["District Number"]
            cursor.updateRow(row)
            
    #Adds the out_table as a layer file to the contents pane in my map
    aprx = arcpy.mp.ArcGISProject(currentdir + "\\SC_Redistricting_Updated.aprx")
    aprxMap = aprx.listMaps("Map")[0] 
    layername = out_table.replace(path+'\\','')
    layer = aprxMap.listLayers(layername)
    if not layer: #if the layer currently does not exist in the table of contents:
        aprxMap.addDataFromPath(out_table)
    aprx.save()
    
    #Updates Symbology
    lyr = aprxMap.listLayers()[0]
    sym = lyr.symbology
    sym.updateRenderer('UniqueValueRenderer')
    sym.renderer.fields = ['Dist_Assgn']
    lyr.symbology = sym
    aprx.save()
    
    now = datetime.datetime.now()
    arcprint("Finishing date and time : {0}",now.strftime("%Y-%m-%d %H:%M:%S"))
    
    
#END FUNCTIONS    
if __name__ == "__main__":
    main()
                