# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 16:52:28 2021

@author: blake
"""
### IMPORTANT ASSUMPTION: WE ASSUME THAT THE FIRST COLUMN OF THE FEATURE LAYER
### IS AN ID COLUMN THAT UNIQUELY LABELS EACH ROW WITH THE NUMBERS 1-X, WHERE
### X IS THE NUMBER OF ROWS

#TO DO LIST
"#1. Change argv stuff --- DONE (Blake)"
#2. Consider new starting temperatures and whatnot
#3. Use build-balanced-zones
#4. Figure out what to do with x
#5. Need to update boundary list with each pass through the code
#6. Need to measure initial energy
#7. Need to generalize odn stuff
#8. Consider adjusting smallest possible temperature

import arcpy,math,os,sys
import random
#seed = 1738
#random.seed(seed)
import CreateSpanningTree
import networkx as nx

def FieldCheck(in_table):
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
    
def acceptchange(T,hypsumpop,hypstateG,hypG,dist1,dist2,nlf,neighbor_list):
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
    return(T,sumpop,stateG,neighbor_list)
        
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
    currentdir = os.getcwd()
    path = currentdir + "\\SC_Redistricting_Updated.gdb"
    arcpy.env.workspace = path
    
    arcpy.env.overwriteOutput = True
    
    global coolingrate
    
    try: #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
        in_table = sys.argv[1]
        sf_pop_field = sys.argv[2]
        sf_name_field = sys.argv[3]
        distcount = int(sys.argv[4])
        MaxIter = int(sys.argv[5])
        T = float(sys.argv[6])
        coolingrate = float(sys.argv[7])
        tol = float(sys.argv[8])
        neighbor_list = sys.argv[9]
        maxstopcounter = sys.argv[10]
    except IndexError: 
        try: #Second, tries to take input from explicit input into main()
            in_table = args[0]
            sf_pop_field = args[1]
            sf_name_field = args[2]
            distcount = int(args[3])
            MaxIter = int(args[4])
            T = float(args[5])
            coolingrate = float(args[6])
            tol = float(args[7])
            neighbor_list = args[8]
            maxstopcounter = args[9]
        except IndexError: #Finally, manually assigns input values if they aren't provided
            in_table=path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1"
            sf_pop_field = "SUM_Popula"
            sf_name_field = "OBJECTID"
            distcount=7
            MaxIter=10
            T = 123000+149000 #Initial Temperature = stdev(pop) + mean pop 
            coolingrate = 0.9975
            tol=30
            neighbor_list=path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1_neighbor_list_shapes"
            maxstopcounter=100
            arcprint("We are using default input choices")
    
    #MIGHT WANT TO MAKE OUT_TABLE HAVE A UNIQUE NAME
    out_table = in_table + "_BuildBalancedZones"
    no_of_dists=0
    while no_of_dists!=distcount:
        no_of_dists=0
        arcprint("Running BuildBalancedZones...")
        arcpy.stats.BuildBalancedZones(in_table,out_table,"NUMBER_OF_ZONES",distcount,None,None,"CONTIGUITY_EDGES_ONLY",None, "COMPACTNESS",[[sf_pop_field,"average"]])
        with arcpy.da.SearchCursor(out_table, "ZONE_ID") as cursor:
            for row in cursor:
                if no_of_dists<row[0]:
                    no_of_dists=int(row[0])
    
    #Returns DistField "Dist_Assgn" and creates the field if it's not already there
    DistField = FieldCheck(out_table)
    #arcprint("DistField is {0}",DistField)
    
    
    
### THIS IS FOR PROOF OF CONCEPT. TO BE REPLACED BY 'BUILD BALANCED ZONES' LATER
    with arcpy.da.UpdateCursor(out_table, ["Dist_Assgn","ZONE_ID"]) as cursor:
        for row in cursor:
            row[0] = row[1]
            cursor.updateRow(row)
    
    
    
    """NEXT FEW LINES SHOULD BE CHANGED SO THAT RANDOM DISTRICTING IS RUN INSTEAD"""
      
    #Counts number of rows in out_table      
    row_count = arcpy.GetCount_management(out_table).getOutput(0) #getOutput(0) returns the value at the first index position of a tool.
    row_count=int(row_count)
    
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
    with arcpy.da.SearchCursor(out_table, [sf_pop_field,DistField]) as cursor:
        for row in cursor:
            #i = district number minus 1, since district numbers range from 1 to 7
            i = row[1]-1
            i = int(i)
            sumpop[i] = row[0] + sumpop[i]
    arcprint("The sum of polygon populations (i.e. sumpop) is {0}.",sumpop)
    idealpop=sum(sumpop)/distcount    
    deviation =[0]*(MaxIter+1)        
    deviation[0] = DeviationFromIdealPop(sumpop, idealpop, distcount)
    
    #Initializes neighbor_list so that each entry in src_dist and nbr_dist is reset to match original districts
    lstFields = arcpy.ListFields(neighbor_list)
    orig_dist_names=[]
    for field in lstFields:
        if field.name in ["src_CLUSTER_ID", "src_Dist_Assgn", "nbr_CLUSTER_ID", "nbr_Dist_Assgn"]:
            orig_dist_names.append(field.name)
    odn=orig_dist_names #An alias
    arcprint("odn is {0}",odn)
    with arcpy.da.UpdateCursor(neighbor_list, [odn[0],odn[1],'src_dist', 'nbr_dist']) as cursor:
        for row in cursor:
            row[2]=row[0] #src_dist = src_CLUSTER_ID
            row[3]=row[1] #nbr_dist = nrb_CLUSTER_ID
            cursor.updateRow(row)
    
#    #Maybe delete x from below
#    [NameField,x] = FindNamingFields(out_table)
#    NameField = NameField[0]
#    arcprint("The NameField is '{0}'",NameField)
    hypsumpop=sumpop.copy()
    stateG = nx.Graph()
    
    #Starting the main line of the Simulated Annealing Algorithm
    count = 0 #The number of iterations in which a change was made
    stopcounter=0 #The number of consecutive iterations in which a change was NOT made
    
    while T>0.1 and count <MaxIter and stopcounter<maxstopcounter:
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
#            hypstateG = nx.Graph()
            [dist1_pop, dist2_pop,hypstateG, hypG,nlf] = CreateSpanningTree.main(out_table,sf_pop_field,sf_name_field,tol,neighbor_list, dist1, dist2, stateG)
#            arcprint("(SA) Edges of G are {0}",hypG.edges)
#            arcprint("(SA) Vertices of G are {0}",hypG.nodes)
        except RuntimeError: #Cuts the code if we encounter a Runtime error in CreateSpanningTree
            arcprint("We had a runtime error. Selecting new districts")
            count=count-1
            stopcounter +=1
            continue
        if dist1_pop==float('inf') or dist2_pop==float('inf'):
            count=count-1
            stopcounter+=1
            #arcprint("The populations were infinity")
            continue
        hypsumpop[dist1-1] = dist1_pop
        hypsumpop[dist2-1] = dist2_pop
        deviation[count] = DeviationFromIdealPop(hypsumpop,idealpop,distcount)
        #arcprint("absolute deviation is {0}",deviation[count])    
        DeltaE = deviation[count] - deviation[count-1]
        arcprint("DeltaE = {0}. T = {1}",DeltaE,T)
        if DeltaE <0: #An improvement!
            [T,sumpop,stateG,neighbor_list] = acceptchange(T,hypsumpop,hypstateG,hypG,dist1,dist2,nlf,neighbor_list)
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
                [T,sumpop,stateG,neighbor_list] = acceptchange(T,hypsumpop,hypstateG,hypG,dist1,dist2,nlf,neighbor_list)
                stopcounter=0
                continue
            else: #undoes the district changes previously made. 
                count = count-1
                stateG=nx.Graph()
                stopcounter+=1
                arcprint("The change was rejected.")
                
        
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
                with arcpy.da.UpdateCursor(out_table, [NameField, DistField, PopField],"{0} = '{1}'".format(NameField,randshape)) as cursor:
                    for row in cursor:
                        row[1] = currdist
                        cursor.updateRow(row)'''
    if T<=0.1:
        arcprint("\nSmallest legal temperature reached T = {0}.", T)
    if count >=MaxIter:
        arcprint("\nMaximum number of iterations reached. count = {0} and MaxIter = {1}", count, MaxIter)
    if stopcounter ==maxstopcounter:
        arcprint("\nWe failed in {0} consecutive ReCom attempts, so we will stop here.",maxstopcounter)
    arcprint("Original deviation = {0}. Final deviation = {1}",deviation[0],deviation[count])
    arcprint("sumpop is {0}",sumpop)
    
    #Repopulates stateG if it was emptied during a rejection step in the algorithm
    distnum = {} #Initializes a dictionary that will contain the district number for each polygon
    popnum = {} #Initializes a dictionary that will contain the population for each polygon
    if nx.is_empty(stateG)==True:
        with arcpy.da.SearchCursor(out_table,[sf_name_field,sf_pop_field]) as cursor:
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
    with arcpy.da.UpdateCursor(out_table,[sf_name_field,"Dist_Assgn"]) as cursor:
        for row in cursor:
            objid= row[0]
            row[1] = stateG.nodes[objid]["District Number"]
            cursor.updateRow(row)
            
#    #Adds the map to the Contents pane      
#    m = arcpy.mp.ArcGISProject("CURRENT").activeMap #Finds active map. 
#    addTab = arcpy.mp.Table(path + "\\" + out_table)
#    m.addTable(addTab) #Adds table to Table of Contents
            
    #Adds the out_table as a layer file to the contents pane in my map
    aprx = arcpy.mp.ArcGISProject(currentdir + "\\SC_Redistricting_Updated.aprx")
    aprxMap = aprx.listMaps("Map")[0] 
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
                