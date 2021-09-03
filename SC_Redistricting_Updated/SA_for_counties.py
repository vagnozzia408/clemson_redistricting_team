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
#13. Reconsider starting temperatures so that 

import arcpy,math,os,sys
import random
seed = 1743
random.seed(seed)
import CreateSpanningTree
import FindBoundaryShapes
import networkx as nx
import GraphMeasures
import numpy as np

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

def AddDistField(in_table):
    lstFields = arcpy.ListFields(in_table)
    DistField = "Dist_Assgn"
    x = False
    for field in lstFields:
        if field.name == "Dist_Assgn":
            x = True
    if x != True:
        arcprint("Field does not exist. Adding Dist_Assgn")
        arcpy.AddField_management(in_table, "Dist_Assgn", "SHORT", field_alias="DIST_ASSIGNMENT")
    return(DistField)    

def DeviationFromIdealPop(sumpop,idealpop,distcount):
    """Returns a single positive integer that sums each district's deviation from the ideal population. Lower numbers for 'deviation' are better. A value of zero would indicate that every district has an equal number of people"""
    absdev = [0 for i in range(distcount)]
    
    for i in range(distcount):
        absdev[i] = abs(sumpop[i]-idealpop)
    deviation_ = sum(absdev)
    deviation_ = round(deviation_)
    return(deviation_)
        
#def FindBoundaryShapes(in_table,neighbor_list):
#    if neighbor_list == None:
#        uniquename = arcpy.CreateUniqueName(in_table + "_neighbor_list")
#        arcpy.PolygonNeighbors_analysis(in_table, uniquename,None,None,None,None,"KILOMETERS")

#%%NO LONGER USED   
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
    
#def ComputeHypComp(dist1, dist2, outDistrictStats):
#    DistrictStats = GraphMeasures.PolsbyPopperUpdate(dist1,dist2,out_table, path, DistrictStats)
#    return(DistrictStats)
    
#%%
    
def acceptchange(T,hypsumpop,hypstateG,hypG,dist1,dist2,nlf,neighbor_list,out_table,DistField,DistrictStats):
    T=T*coolingrate
    sumpop = hypsumpop.copy()
    stateG = hypstateG.copy()
    arcprint("The change was accepted!")
    
    #Updates the neighbor list table after each iteration
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
    DistrictStats[dist1-1].ConfirmStats(True)
    DistrictStats[dist2-1].ConfirmStats(True)
    
    arcprint("The stats for district 1 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[0].Area, DistrictStats[0].Perimeter, DistrictStats[0].ppCompactScore)
    arcprint("The stats for district 2 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[1].Area, DistrictStats[1].Perimeter, DistrictStats[1].ppCompactScore)
    arcprint("The stats for district 3 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[2].Area, DistrictStats[2].Perimeter, DistrictStats[2].ppCompactScore)
    arcprint("The stats for district 4 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[3].Area, DistrictStats[3].Perimeter, DistrictStats[3].ppCompactScore)
    arcprint("The stats for district 5 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[4].Area, DistrictStats[4].Perimeter, DistrictStats[4].ppCompactScore)
    arcprint("The stats for district 6 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[5].Area, DistrictStats[5].Perimeter, DistrictStats[5].ppCompactScore)
    arcprint("The stats for district 7 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[6].Area, DistrictStats[6].Perimeter, DistrictStats[6].ppCompactScore)
    
    return(T,sumpop,stateG,neighbor_list,DistrictStats)
        
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
        arcprint("We are running this from inside ArcGIS")
    else:
        runspot = "console"
        arcprint("We are running this from the python console")   
            
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
        coolingrate = float(sys.argv[7])
        tol = float(sys.argv[8])
        #neighbor_list = sys.argv[9]
        maxstopcounter = sys.argv[10]
    except IndexError: 
        try: #Second, tries to take input from explicit input into main()
            in_table = args[0]
            in_pop_field = args[1]
            in_name_field = args[2]
            distcount = int(args[3])
            MaxIter = int(args[4])
            T = float(args[5])
            coolingrate = float(args[6])
            tol = float(args[7])
            #neighbor_list = args[8]
            maxstopcounter = args[9]
        except IndexError: #Finally, manually assigns input values if they aren't provided
            in_table=path+"\\SC_Counties_2020"
            in_pop_field = "SUM_Popula"
            in_name_field = "OBJECTID"
#            in_table = path + "\\Precincts_2020"
#            in_pop_field = "Precinct_P"
#            in_name_field = "OBJECTID_1"
            distcount=7
            MaxIter=10
            ###INITIAL TEMPS NEED TO BE ADJUSTED
#            T = 123000+109000 #Initial Temperature = stdev(pop) + mean pop  #FOR COUNTIES
#            T = 1300+2200  #Initial Temperature = stdev(pop) + mean pop  #FOR PRECINCTS
            T = 10
            coolingrate = 0.999
            tol=30
            #neighbor_list=path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1_neighbor_list_shapes"
            maxstopcounter=100
            arcprint("We are using default input choices")
    
    
    
    #This builds alpha, which is the normalized unit vector that details how much we care about any given metric. 
    metric_count = 2
    #metric_count = 3
    alpha = metric_count*[0]
    for i in range(metric_count):
        alpha[i] = random.randint(1,1000)
    tot = sum(alpha)
    for i in range(metric_count):
        alpha[i] = alpha[i]/tot
        
    #Normalizing factor
    global prev_DeltaE
    prev_DeltaE = np.zeros([5,metric_count],dtype=float)
    global norm
    norm = [0]*metric_count
    
    #Counts number of rows in out_table      
    row_count = arcpy.GetCount_management(in_table).getOutput(0) #getOutput(0) returns the value at the first index position of a tool.
    row_count=int(row_count)
    
    #MIGHT WANT TO MAKE OUT_TABLE HAVE A UNIQUE NAME
    out_table = in_table + "_SA_" + "{0}".format(distcount) + "dists"
    #out_table = arcpy.CreateUniqueName(in_table + "_SA")
#    no_of_dists=0
#    while no_of_dists!=distcount:
#        no_of_dists=0
#        arcprint("Running BuildBalancedZones...")
#        #arcpy.stats.BuildBalancedZones(in_table,out_table,"NUMBER_OF_ZONES",distcount,None,None,"CONTIGUITY_EDGES_ONLY",None, None,[[in_pop_field,"average"]])
#        arcpy.stats.BuildBalancedZones(in_table,out_table,"NUMBER_OF_ZONES",distcount,None,None,"CONTIGUITY_EDGES_ONLY",None, None,None)
#        #The following code ensures that exactly distcount districts were created
#        with arcpy.da.SearchCursor(out_table, "ZONE_ID") as cursor:
#            for row in cursor:
#                if no_of_dists<row[0]:
#                    no_of_dists=int(row[0])
    
    
    
    #Trying to use Spatially Constrained Multivariate Clustering instead of BBZ
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
    
    #Creates a column named "temp_dist" and zeros it out
    if not arcpy.ListFields(out_table, "temp_dist"):
        arcpy.AddField_management(out_table, "temp_dist", "SHORT", field_alias="Temporary District")
    with arcpy.da.UpdateCursor(out_table, "temp_dist") as cursor:
        for row in cursor: 
            row[0] = 0
            cursor.updateRow(row)
    
    FindBoundaryShapes.main(out_table)
    #global neighbor_list
    neighbor_list = out_table + "_nbr_list"
    
    #Returns DistField "Dist_Assgn" and creates the field if it's not already there
    DistField = AddDistField(out_table)

    # Copies all CLUSTER_ID's into Dist_Assgn
    with arcpy.da.UpdateCursor(out_table, [DistField,"CLUSTER_ID"]) as cursor:
        for row in cursor:
            row[0] = row[1]
            cursor.updateRow(row)
      

    
#    #Finds field name for population
#    lstFields = arcpy.ListFields(out_table)
#    PopField = None
#    for field in lstFields:
#        if field.name == "SUM_Popula" or field.name == "Precinct_P":
#            PopField = field.name
#            break
#    if PopField == None:
#        arcerror("PopField is empty. Neither 'SUM_Popula' nor 'Precinct_P' were found as field names.")
    
    #Finds sum of each district population
    sumpop=[]
    sumpop = [0]*distcount
    with arcpy.da.SearchCursor(out_table, [in_pop_field,DistField]) as cursor:
        for row in cursor:
            #i = district number minus 1, since district numbers range from 1 to distcount
            i = row[1]-1
            i = int(i)
            sumpop[i] = row[0] + sumpop[i]
    arcprint("The sum of polygon populations (i.e. sumpop) is {0}.",sumpop)
    idealpop=sum(sumpop)/distcount    
    
    global DistrictStats
   # DistrictStats = [0]*(MaxIter+1)
    DistrictStats = GraphMeasures.main(out_table, "CLUSTER_ID")
    comp = [o.ppCompactScore for o in DistrictStats] #A list of compactness scores
    #global MapStats
    #MapStats = GraphMeasures.main(out_table, "CLUSTER_ID") ## We need to grab the second thing it returns, not DistrictList)
    #fair = MapStats[0].PICKONE
    
    arcprint("The stats for district 1 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[0].Area, DistrictStats[0].Perimeter, DistrictStats[0].ppCompactScore)
    arcprint("The stats for district 2 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[1].Area, DistrictStats[1].Perimeter, DistrictStats[1].ppCompactScore)
    arcprint("The stats for district 3 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[2].Area, DistrictStats[2].Perimeter, DistrictStats[2].ppCompactScore)
    arcprint("The stats for district 4 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[3].Area, DistrictStats[3].Perimeter, DistrictStats[3].ppCompactScore)
    arcprint("The stats for district 5 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[4].Area, DistrictStats[4].Perimeter, DistrictStats[4].ppCompactScore)
    arcprint("The stats for district 6 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[5].Area, DistrictStats[5].Perimeter, DistrictStats[5].ppCompactScore)
    arcprint("The stats for district 7 are: Area = {0}, Perimeter = {1}, PP = {2}", DistrictStats[6].Area, DistrictStats[6].Perimeter, DistrictStats[6].ppCompactScore)
    
    #arcprint("The fairness scores for this map are: Median_Mean = {0}, EfficiencyGap = {1}, B_G = {2}", MapStats[0].MedianMean, MapStats[0].EG, MapStats[0].B_G)
    
    deviation =[0]*(MaxIter+1)
    global avgcomp
    avgcomp = [0]*(MaxIter+1)  
    #global FairScore
    #fairscore = [0]*(MaxIter+1)
    deviation[0] = DeviationFromIdealPop(sumpop, idealpop, distcount)
    avgcomp[0] = sum(comp)/len(comp)
    #fairscore[0] = fair
    
    
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
        if count == 20:
            arcprint("count is 20")
        count = count+1
        dist1 = random.randint(1,distcount)
        dist2 = random.randint(1,distcount)
        while dist1==dist2: #Randomly selects two different districts
            dist1 = random.randint(1,distcount)
            dist2 = random.randint(1,distcount)
        arcprint("dist1 = {0} and dist2 = {1}.", dist1,dist2)
        try:
            [dist1_pop, dist2_pop, hypstateG, hypG, nlf, prevdists] = CreateSpanningTree.main(out_table, in_pop_field, "SOURCE_ID", tol, neighbor_list, dist1, dist2, stateG)
        except RuntimeError: #Cuts the code if we encounter a Runtime error in CreateSpanningTree
            arcprint("We had a runtime error. Selecting new districts")
            count -= 1
            stopcounter += 1
            continue
        except SystemError:
            arcprint("We had a system error. Selecting new districts")
            count -= 1
            stopcounter += 0 #We don't want non-adjacent district choices to contribute to stopcounter
            continue
        if dist1_pop==float('inf') or dist2_pop==float('inf'):
            count-=1
            stopcounter+=1
            continue
        hypsumpop[dist1-1] = dist1_pop
        hypsumpop[dist2-1] = dist2_pop
        deviation[count] = DeviationFromIdealPop(hypsumpop,idealpop,distcount)
        DistrictStats = GraphMeasures.PolsbyPopperUpdate(dist1,dist2, out_table,path, DistrictStats)
        hypcomp = [o.HypppCompactScore for o in DistrictStats] #A list of compactness scores
        avgcomp[count] = sum(hypcomp)/len(hypcomp)
        #MapStats.append(GraphMeasures.Map(count))
        #MapStats[-1].GraphMeasures.UpdateMapStats(DistrictStats)
        
        
        #arcprint("absolute deviation is {0}",deviation[count])    
        DeltaE_dev = deviation[count] - deviation[count-1]
        DeltaE_comp = avgcomp[count] - avgcomp[count-1]
        #DeltaE_fair = fairscore[count] - fairscore[count -1]
        arcprint("DeltaE_dev = {0}.",DeltaE_dev)
        arcprint("DeltaE_comp = {0}.",DeltaE_comp)
        #arcprint("DeltaE_fair = {0}.", DeltaE_fair)
        
        prev_DeltaE[count % 5][0] = abs(DeltaE_dev)
        prev_DeltaE[count % 5][1] = abs(DeltaE_comp)
        #prev_DeltaE[count % 5][2] = abs(DeltaE_fair)
        for i in range(metric_count):
            norm[i] = sum(prev_DeltaE[:,i])/len(prev_DeltaE[:,i])
        
        #Calculates DeltaE based on each of the metrics_
        DeltaE = DeltaE_dev*alpha[0]/norm[0]+ DeltaE_comp*alpha[1]/norm[1]
        #DeltaE = DeltaE_dev*alpha[0]/norm[0]+ DeltaE_comp*alpha[1]/norm[1] + DeltaE_fair*alpha[2]/norm[2]
        arcprint("DeltaE = {0}. T = {1}.",DeltaE,T)
        
        
        if DeltaE <0: #An improvement!
            [T,sumpop,stateG,neighbor_list,DistrictStats] = acceptchange(T,hypsumpop,hypstateG,hypG,dist1,dist2,nlf,neighbor_list,out_table,DistField,DistrictStats)
            stopcounter=0
            continue
        else : #A worsening :(
            rand = random.uniform(0,1)
            try: 
                p = 1/math.exp(DeltaE/T) #p = probability that the worsening is accepted
            except OverflowError:
                p = 0 #If denominator in calculation above is large enough, an OverflowError will occur
            arcprint("p = {0}. rand = {1}",p,rand)
            if rand<=p: #Worsening is accepted
                [T,sumpop,stateG,neighbor_list,DistrictsStats] = acceptchange(T,hypsumpop,hypstateG,hypG,dist1,dist2,nlf,neighbor_list,out_table,DistField,DistrictStats)
                stopcounter=0 #resets the stopcounter
                continue
            else: #undoes the district changes previously made. 
                count = count-1
                nx.set_node_attributes(stateG,prevdists,"District Number")
                stopcounter+=1
                arcprint("The change was rejected, since p < rand.")
                
        
        
    if T<=0.1:
        arcprint("\nSmallest legal temperature reached T = {0}.", T)
    if count >=MaxIter:
        arcprint("\nMaximum number of iterations reached. count = {0} and MaxIter = {1}", count, MaxIter)
    if stopcounter ==maxstopcounter:
        arcprint("\nWe failed in {0} consecutive ReCom attempts, so we will stop here.",maxstopcounter)
    arcprint("Original population deviation from ideal = {0}. Final population deviation = {1}",deviation[0],deviation[count])
    arcprint("Original Polsby Popper Compactness = {0}. Final Compactness = {1}",avgcomp[0],avgcomp[count])
    arcprint("The population of each district is {0}",sumpop)
    arcprint("The compactness of each district is {0}",[o.ppCompactScore for o in DistrictStats])
    
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
    
    
#END FUNCTIONS    
if __name__ == "__main__":
    main()
                