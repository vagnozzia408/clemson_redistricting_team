# -*- coding: utf-8 -*-
"""
Created on Wed Jun 23 18:21:17 2021

@author: Blake Splitter and Amy Burton

This code should be designed to
take in a graph G=(V,E) and two adjacent districts. Then a subgraph imposed on
the nodes of those two districts will be constructed. Thereafter, we will create
a spanning tree on the resulting subgraph.
"""

###TO DO:
"#1. Change asterisk on 'with .... as cursor:' line to include actual field names --- DONE (Blake). "
"#2. Validate that districts are adjacent (Working code in rows 60-106) --- DONE (Amy)."
"#3. Figure out how to adjust script validation in ArcGIS Pro so that methodtype changes the rest of the input. --- CONCLUDED. Determined unnecessary (Blake)" 
#4. Edit "with .... as cursor:" line to include more robust SQL statement.
#5. Currently, this code assumes that our neighbor list include both sides of every edge. Should we build it so that it doesn't necessarily assume that?
"#6. Probably need to hard-code Wilson's algorithm --- DONE (Blake). Taken from Greg's code."
"#7. Need to determine how to split the spanning tree into two pieces and recover the two pieces. IDEA: maybe networkx has some functionality that will let it determine which edges are in which tree --- DONE (Blake)"
"#8. Allow Python users to specify input easily. --- DONE (Input can be specified if running this function from a different script by calling CreateSpanningTree.main(***insert args here***), Blake)"
"#9. Find an easier way to determine whether we're running from within Python or ArcGIS --- DONE. Now the code checks what sys.executable is, rather than examining argument input. (Blake)"
"#10. Generalize field names for 'shapefile' --- DONE. These are now user inputs"
#11. Figure out how to cut edges and find subtree efficiently.
#12. Consider how to change ideal population number as algorithm progresses
"#13. In nbrlist_fields, account for the 'nodes' column too and adjust the code so that shapes adjacent by a point are not adjacent --- DONE. Nodes are now accounted for"
"#14. Allow stateG to be a proper input parameter --- DONE."
#15. Decide whether idealpop should be used in FindEdgeCut

import arcpy, os, sys
import random
seed = 1743
random.seed(seed)
#from random import randint
import networkx as nx
#from openpyxl import load_workbook
#import numpy ### WE SHOULD TRY TO USE ONLY 'RANDOM' IF WE CAN

runspot = None #Global variable that will determine whether the code is started from ArcGIS or the Python console

def FindNamingFields(in_table):
    lstFields = arcpy.ListFields(in_table)
    namefields=[]
    distfields=[]
    for field in lstFields:
        #if field.name in  ["GEOID20", "Name20", "NAME20", "Name", "FID", "SOURCE_ID"]:
        if field.name in  ["src_GEOID20", "src_OBJECTID", "src_FID", "src_SOURCE_ID", "nbr_GEOID20", "nbr_OBJECTID", "nbr_FID", "nbr_SOURCE_ID"]:
            namefields.append(field.name)
        if field.name in ["src_dist", "nbr_dist"]:
            distfields.append(field.name)
        if field.name == "NODE_COUNT":
            distfields.append(field.name)
    nbrlist_fields = [item for sublist in [namefields, distfields] for item in sublist]
    return(namefields,distfields,nbrlist_fields)

def loopErasedWalk(graph, rng, v1 = None, v2 = None):
    '''Returns a loop-erased random walk between components v1 & v2'''
    if v1 is None:
        v1 = [rng.choice(sorted(list(graph.nodes)))]
    if v2 is None:
        v2 = [rng.choice(sorted(list(graph.nodes)))]

    v = rng.choice(sorted(v1))
    walk = [v]
    while v not in v2:
        v = rng.choice(sorted(list(graph.neighbors(v))))
        if v in walk:
            walk = walk[0:walk.index(v)]
        walk.append(v)

    return walk

def wilson(graph, rng):
    '''Returns a uniform spanning tree on G'''
    walk = loopErasedWalk(graph, rng)
    currentNodes = [n for n in walk]

    uniformTree = nx.Graph()
    for i in range(len(walk)-1):
        uniformTree.add_edge(walk[i], walk[i+1])

    treeNodes = set(uniformTree.nodes)
    neededNodes = set(graph.nodes) - treeNodes

    while neededNodes:
        v = rng.choice(sorted(list(neededNodes))) # sort for code repeatability
        walk = loopErasedWalk(graph, rng, v1 = [v], v2 = currentNodes)
        currentNodes += walk
        for i in range(len(walk)-1):
            uniformTree.add_edge(walk[i], walk[i+1])
        treeNodes = set(uniformTree.nodes)
        neededNodes = set(graph.nodes) - treeNodes

    return uniformTree

def FindEdgeCut(tree,tol,criteria):
    '''Input a tree graph, a percent tolerance, and a criteria for the graph. The function will remove a 
    random edge that splits the tree into two pieces such that each piece 
    has criteria (like population) within that percent tolerance. The variable 'tol' should be a positive real 
    number in (0,100]. The criteria should be string that labels an attribute of the nodes of the tree.'''
    if tol > 100 or tol <=0 or (isinstance(tol,float)==False and isinstance(tol,int)==False): 
        arcerror("tol must be a float or integer variable in the range (0,100].")
    if nx.is_tree(tree) == False:
        arcerror("The input graph must be a tree.")
    if isinstance(criteria,str)==False:
        arcerror("The criteria input should be a string.")
    tree_edge_list = list(tree.edges)
    random.shuffle(tree_edge_list) #Randomly shuffles the edges of T
    e=None
    TELL= len(tree_edge_list) #TELL = Tree Edge List Length
    
    for i in range(TELL):
        e = tree_edge_list[i] #Edge to delete
        tree.remove_edge(*e)
        #arcprint("The edges of T are now {0}. We just deleted {1}.",tree.edges,e)
        subgraphs = nx.connected_components(tree)
        subgraphs_lst = list(subgraphs)
        subgraphs_lst[0] = sorted(subgraphs_lst[0])
        subgraphs_lst[1] = sorted(subgraphs_lst[1])
        #arcprint("The subgraph candidates are {0}.",subgraphs_lst)
        dist_crit1 = sum(value for key, value in nx.get_node_attributes(tree,criteria).items() if key in subgraphs_lst[0]) #Finds population sum for first district
        dist_crit2 = sum(value for key, value in nx.get_node_attributes(tree,criteria).items() if key in subgraphs_lst[1]) #Finds population sum for second district
#        if criteria == "Population":
#            total_crit = 2*idealpop
#        else:
        total_crit= dist_crit1+dist_crit2
        if abs(dist_crit1 - total_crit/2) > 0.01*tol*(total_crit/2):
            tree.add_edge(*e) #Adds the edge back to the tree if it didn't meet the tolerance
        else:
            #arcprint("Criteria requirement was met. Removing edge {0}. Required {1} iteration(s).\nThe two subgraphs are {2}, with {3} of {4} and {5}, respectively.",e,i+1,subgraphs_lst,criteria,int(dist_crit1),int(dist_crit2))
            return(dist_crit1,dist_crit2,subgraphs_lst)
        if i==TELL-1:
            arcprint("No subgraphs with appropriate criteria requirements were found.\n")
            return(float('inf'), float('inf'),[]) 

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

#Same as arcerror, but raises a different type of error.         
def arcerror2(message,*variables):
    '''Prints an error message using arcpy.AddError() unless it can't; then it uses print. '''
    if runspot == "ArcGIS":
        arcpy.AddError(message.format(*variables))
    elif runspot == "console":
        newmessage=message
        j=0
        while j<len(variables): #This while loop puts the variable(s) in the correct spot(s) in the string
            newmessage = newmessage.replace("{"+str(j)+"}",str(variables[j])) #Replaces {i} with the ith variable
            j=j+1
        raise SystemError(newmessage)
    else: 
        raise SystemError("No value for runspot has been assigned")

#%% MAIN CODE STARTS HERE
def main(*args):
    
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
    arcpy.env.workspace = path
    
    arcpy.env.overwriteOutput = True
    
    try: #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
        shapefile=sys.argv[1]
        sf_pop_field = sys.argv[2]
        sf_name_field = sys.argv[3]
        tol=float(sys.argv[4])
        neighbor_list = sys.argv[5]
        dist1=int(sys.argv[6])
        dist2=int(sys.argv[7])
        stateG = sys.argv[8]
        p_list = sys.argv[9]
        #idealpop=float(sys.argv[7])
        del stateG #We can't insert a graph from the ArcGIS input line
        arcprint("Running CreateSpanningTree from command line arguments")
    except IndexError: 
        try: #Second, tries to take input from explicit input into main()
            shapefile = args[0]
            sf_pop_field = args[1]
            sf_name_field = args[2]
            tol = float(args[3])
            neighbor_list = args[4]
            dist1 = int(args[5])
            dist2 = int(args[6])
            stateG = args[7]
            p_list = args[8]
            #idealpop = args[8]
            arcprint("Running CreateSpanningTree using input from another script")
        except IndexError: #Finally, manually assigns input values if they aren't provided
            shapefile=path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1"
            sf_pop_field = "SUM_Popula"
            sf_name_field = "OBJECTID"
            tol=30
            neighbor_list=path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1_neighbor_list_shapes"
            dist1=6
            dist2=4
            p_list = [[]] * 7
            #idealpop = 717252
            arcprint("Running CreateSpanningTree using default input choices")

    #arcprint("sf_pop_field is {0} and is type {1}",sf_pop_field, type(sf_pop_field))
   
    try: 
        prevdists = {}
        prevdists = stateG.nodes("District Number")
        prevdists = dict(prevdists)
        #stateG = stateG #Doesn't do anything, but if stateG doesn't exist, it will produce an UnboundLocalError
    except UnboundLocalError:
        #global stateG ## Maybe unnecessary?
        stateG = nx.Graph() #Creates an empty graph that will contain all adjacencies for the state
    
    if dist1==dist2:
        arcerror2("The districts must be different. Currently, dist1={0} and dist2={1}.",dist1,dist2) #Creates an error if the two district choices are the same

    #Creates a column named "temp_dist" and zeros it out
    if not arcpy.ListFields(shapefile, "temp_dist"):
        arcpy.AddField_management(shapefile, "temp_dist", "SHORT", field_alias="Temporary District")
    if __name__ == "__main__":
        with arcpy.da.UpdateCursor(shapefile, "temp_dist") as cursor:
            for row in cursor: 
                row[0] = 0
                cursor.updateRow(row)
    
    #Adds src_dist and nbr_dist to neighbor_list if they don't already exist. These fields will be the ones that change mid-algorithm
    if not arcpy.ListFields(neighbor_list, "src_dist"):
        arcpy.AddField_management(neighbor_list, "src_dist", "SHORT", field_alias="Source District")
        arcpy.AddField_management(neighbor_list, "nbr_dist", "SHORT", field_alias="Neighbor District")
    lstFields = arcpy.ListFields(neighbor_list) #Updates lstFields
    orig_dist_names=[]
    lstFields = arcpy.ListFields(neighbor_list)
    for field in lstFields:
        if field.name in ["src_CLUSTER_ID", "src_Dist_Assgn", "src_ZONE_ID", "nbr_CLUSTER_ID", "nbr_ZONE_ID", "nbr_Dist_Assgn"]:
            orig_dist_names.append(field.name) #Creats a list that has the original field names that describe the district the polygons are in
    odn=orig_dist_names #An alias
    
    #Resets the src_dist and nbr_dist columns if they are empty or if this script is run as a stand-alone
    if not arcpy.ListFields(neighbor_list, "src_dist") or __name__ == "__main__": 
        with arcpy.da.UpdateCursor(neighbor_list, [odn[0],odn[1],'src_dist', 'nbr_dist']) as cursor:
            for row in cursor:
                row[2]=row[0] #src_dist = src_CLUSTER_ID
                row[3]=row[1] #nbr_dist = nbr_CLUSTER_ID
                cursor.updateRow(row)
            del row
        del cursor
    
    [namefields,distfields,nbrlist_fields] = FindNamingFields(neighbor_list) #Finds field names for neighbor_list
    nlf = nbrlist_fields #An alias
    

    #Determines if two districts are adjacent with a boundary larger than a single point
    AdjFlag=0
    with arcpy.da.SearchCursor(neighbor_list, nlf, '''{}={} AND {}={} AND {}={}'''.format("src_dist",dist1,"nbr_dist",dist2,"NODE_COUNT",0)) as cursor:
        for row in cursor:
            AdjFlag+=1
            if AdjFlag>=1:
                arcprint("Adjacency Established between districts {0} and {1} by units {2} and {3}", dist1, dist2, row[0],row[1])
                break
    del cursor

    if AdjFlag==0: 
        arcprint("Districts {0} and {1} are not adjacent.",dist1, dist2)
        arcerror2("")
    

    ## Where Amy's code edits end.
    
    Cur_P_List = []
    Cur_P_List.extend(p_list[dist1-1])
    Cur_P_List.extend(p_list[dist2-1])
    Cur_P_List.sort()
    
    arcprint("Before Recom Dist1 and Dist2 have a combined ({0} + {1}) {2} precints: {3}", len(p_list[dist1-1]), len(p_list[dist2-1]), len(Cur_P_List))
    
    G = nx.Graph() #Creates an empty graph that will contain adjacencies for the two districts
    distnum = {} #Initializes a dictionary that will contain the district number for each polygon
    popnum = {} #Initializes a dictionary that will contain the population for each polygon
    
    if nx.is_empty(stateG)==True:
        with arcpy.da.SearchCursor(shapefile,[sf_name_field,sf_pop_field]) as cursor:
            for row in cursor:
                popnum[row[0]] = row[1] #Finds population of each polygon
                stateG.add_node(row[0]) #Adds each polygon to the node list for stateG
                del row
            del cursor
        with arcpy.da.SearchCursor(neighbor_list,nbrlist_fields) as cursor:
            for row in cursor:
                cursor.reset
                if list(stateG.edges).count([row[0],row[1]])==0 and list(stateG.edges).count([row[1],row[0]])==0:
                    stateG.add_edge(row[0],row[1])
                distnum[row[0]]=row[3] #distnum[src_OBJECTID] = src_dist
            del cursor
        nx.set_node_attributes(stateG,popnum,"Population")
        nx.set_node_attributes(stateG,distnum,"District Number")
    nodes_for_G = []

    if distnum == {}:
        distnum = dict(stateG.nodes("District Number"))
    if popnum == {}:
        popnum = dict(stateG.nodes("Population"))
        
    Moving_P_List = []
    #Finds nodes that are in district 1 or district 2
    for v in distnum:
        if distnum[v]==dist1 or distnum[v]==dist2:
            nodes_for_G.append(v)
            Moving_P_List.append(v)
    Moving_P_List.sort()
    arcprint("Number of nodes in this Graph (before subgraphs) #:{0}", len(Moving_P_List))
    
    if Moving_P_List == Cur_P_List:
        arcprint("We have the correct precincts for our subgraphs.")
    elif len(Moving_P_List) == len(Cur_P_List) :
        arcprint("We DO NOT have the correct precincts, but we have the correct number, {0}", len(Moving_P_List))
    elif len(Moving_P_List) != len(Cur_P_List) :
        arcprint("We have {0} more precincts in the subgraphs than we are supposed to", len(Moving_P_List) - len(Cur_P_List))
            
    G = stateG.subgraph(nodes_for_G) #Finds a subgraph containing all adjacencies for vertices in the two districts
    
    #arcprint("Vertices of G are {0}",sorted(G.nodes))
    #arcprint("Edges of G are {0}",sorted(G.edges))

    if nx.is_connected(G) == False:
        arcprint("G is not connected. The connected components are {0}",sorted(list(nx.connected_components(G))))
        sys.exit()
    
    T = wilson(G,random) #Creates a uniform random spanning tree for G using Wilson's algorithm
    #arcprint("T edges are {0}",sorted(T.edges))
    if popnum != {}:   
        nx.set_node_attributes(T,popnum,"Population") 
    else:
        nx.set_node_attributes(T,dict(G.nodes("Population")),"Population")
        
    if distnum != {}:   
        nx.set_node_attributes(T,distnum,"District Number") 
    else:
        nx.set_node_attributes(T,dict(G.nodes("District Number")),"District Number")
        
    [dist1_pop, dist2_pop,subgraphs] = FindEdgeCut(T,tol,"Population") #Removes an edge from T so that the Population of each subgraph is within tolerance (tol)
    
    
    #This next section of code decides which subgraph should become district 1 and which should become district 2
    if dist1_pop!=float('inf') and dist2_pop!=float('inf'):
        s0d1count=0
        s0d2count=0
        s1d1count=0
        s1d2count=0
        for i in subgraphs[0]: 
            if stateG.nodes[i]["District Number"] == dist1:
                s0d1count +=1
            elif stateG.nodes[i]["District Number"] == dist2:
                s0d2count +=1
        for i in subgraphs[1]:
            if stateG.nodes[i]["District Number"] == dist1:
                s1d1count +=1
            elif stateG.nodes[i]["District Number"] == dist2:
                s1d2count +=1
        
        #Assigns either dist1 or dist2 to the changed polygons
        if s0d1count + s1d2count >= s0d2count + s1d1count:
            for i in subgraphs[0]:
                stateG.nodes[i]["District Number"] = dist1
                distnum[i] = dist1
                SG_KEY_FIRST = dist1
            for i in subgraphs[1]:
                stateG.nodes[i]["District Number"] = dist2
                distnum[i] = dist2
            arcprint("Subgraph 0 is the new district {0} and subgraph 1 is the new district {1}",dist1,dist2)
        
        else:
            for i in subgraphs[0]:
                stateG.nodes[i]["District Number"] = dist2
                distnum[i] = dist2
                SG_KEY_FIRST = dist2
            for i in subgraphs[1]:
                stateG.nodes[i]["District Number"] = dist1
                distnum[i] = dist1
            arcprint("Subgraph 0 is the new district {0} and subgraph 1 is the new district {1}",dist2,dist1)
        
        arcprint("Updating temp_dist in CreateSpanningTree.py...")
        arcprint("The subgraphs have {0} and {1} precincts.", len(subgraphs[0]), len(subgraphs[1]))
        Subgraph1Count = 0
        Subgraph2Count = 0
        DontMoveCount = 0
        with arcpy.da.UpdateCursor(shapefile, [sf_name_field,"temp_dist"]) as cursor:
            for row in cursor: 
                if row[0] in subgraphs[0]:
                    if SG_KEY_FIRST == dist1 :
                        row[1] = 1
                        Subgraph1Count += 1
                    else :
                        row[1] = 2
                        Subgraph2Count += 1
                elif row[0] in subgraphs[1]:
                    if SG_KEY_FIRST == dist2 :
                        row[1] = 1
                        Subgraph1Count += 1
                    else :
                        row[1] = 2
                        Subgraph2Count += 1
                elif (row[0] not in subgraphs[0]) and (row[0] not in subgraphs[1]):
                    row[1] = 0
                    DontMoveCount += 1
                else:
                    arcerror2("{0} is not assigned a proper district...", row[0])
                cursor.updateRow(row)
        arcprint("When updating temp_dist we counted the following things: {0} precincts in dist1, {1} precincts in dist2, {2} precints not slated to move, giving us {3} total precincts", Subgraph1Count, Subgraph2Count, DontMoveCount, Subgraph1Count + Subgraph2Count + DontMoveCount)
    #Returns values if this script was called by another script
    if __name__ != "__main__":
        return(dist1_pop, dist2_pop,stateG,G,nlf,prevdists,neighbor_list)

if __name__ == "__main__":
    main()