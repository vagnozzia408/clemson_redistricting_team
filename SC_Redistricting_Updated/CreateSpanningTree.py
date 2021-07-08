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
#2. Validate that districts are adjacent (Working code in rows 60-106)
#3. Figure out how to adjust script validation in ArcGIS Pro so that methodtype changes the rest of the input.
#4. Edit "with .... as cursor:" line to include more robust SQL statement.
#5. Currently, this code assumes that our neighbor list include both sides of every edge. Should we build it so that it doesn't necessarily assume that?
"#6. Probably need to hard-code Wilson's algorithm --- DONE (Blake). Taken from Greg's code."
#7. Need to determine how to split the spanning tree into two pieces and recover the two pieces. IDEA: maybe networkx has some functionality that will let it determine which edges are in which tree
#8. Allow Python users to specify input easily.
#9. Find an easier way to determine whether we're running from within Python or ArcGIS
#10. Generalize field names for 'shapefile'
#11. Figure out how to cut edges and find subtree efficiently.

import arcpy, os
import random
seed = 1738
random.seed(seed)
from random import randint
import networkx as nx
#import numpy ### WE SHOULD TRY TO USE ONLY 'RANDOM' IF WE CAN

runspot = "ArcGIS" #Global variable that will determine whether the code is started from ArcGIS or the Python console

def FindNamingFields(in_table):
    lstFields = arcpy.ListFields(in_table)
    namefields=[]
    distfields=[]
    for field in lstFields:
        #if field.name in  ["GEOID20", "Name20", "NAME20", "Name", "FID", "SOURCE_ID"]:
        if field.name in  ["src_GEOID20", "src_OBJECTID", "src_FID", "src_SOURCE_ID", "nbr_GEOID20", "nbr_OBJECTID", "nbr_FID", "nbr_SOURCE_ID"]:
            namefields.append(field.name)
        if field.name in ["src_CLUSTER_ID", "src_Dist_Assgn", "nbr_CLUSTER_ID", "nbr_Dist_Assgn"]:
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
        arcerror("tol must be a float variable in the range (0,100].")
    if nx.is_tree(tree) == False:
        arcerror("The input graph must be a tree.")
    if isinstance(criteria,str)==False:
        arcerror("The criteria input should be a string.")
    tree_edge_list = list(tree.edges)
    random.shuffle(tree_edge_list) #Randomly shuffles the edges of T
    e=None
    TELL= len(tree_edge_list)
    
    for i in range(TELL):
        e = tree_edge_list[i] #Edge to delete
        tree.remove_edge(*e)
        #arcprint("The edges of T are now {0}. We just deleted {1}.",tree.edges,e)
        subgraphs = nx.connected_components(tree)
        subgraphs_lst = list(subgraphs)
        arcprint("The subgraph candidates are {0}.",subgraphs_lst)
        dist_crit1 = sum(value for key, value in nx.get_node_attributes(tree,criteria).items() if key in subgraphs_lst[0]) #Finds population sum for first district
        dist_crit2 = sum(value for key, value in nx.get_node_attributes(tree,criteria).items() if key in subgraphs_lst[1]) #Finds population sum for second district
        total_crit= dist_crit1+dist_crit2
        #arcprint("The two new district populations are {0} and {1}, for dist1 and dist2, respectively",dist_crit1,dist_crit2)
        if abs(dist_crit1 - total_crit/2) > 0.01*tol*(total_crit/2):
            tree.add_edge(*e)
        else:
            arcprint("Criteria requirement was met. Removing edge {0}. Required {1} iteration(s).\nThe two subgraphs are {2}, with {3} of {4} and {5}, respectively.",e,i,subgraphs_lst,criteria,dist_crit1,dist_crit2)
            break
        if i==TELL-1:
            arcprint("No subgraphs with appropriate criteria requirements were found.\n")

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



currentdir = os.getcwd()
path = currentdir + "\\SC_Redistricting_Updated.gdb"

## The following lines start the structure of repeating iterations by currently keep the script from successfully running inside ArcGIS
StopCriterion = False #Currently runs 3 iterations of successfully finding adjacent districts then quits. 
IterationCount = 0
while StopCriterion == False:

    methodtype = arcpy.GetParameterAsText(0)
    neighbor_list=arcpy.GetParameterAsText(1)
    dist1=arcpy.GetParameterAsText(2)
    dist2=arcpy.GetParameterAsText(3)
    shapefile=arcpy.GetParameterAsText(4)


    if methodtype=='' and neighbor_list=='' and dist1=='' and dist2=='' and shapefile=='':
        methodtype = "Enter Neighbors List"
        neighbor_list=path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1_neighbor_list_shapes"
        #dist1="2"
        dist1=randint(1,7) #Randomly selecting districts
        #dist2="7"
        dist2=randint(1,7) #Randonly selecting districts
        shapefile=path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1"
        runspot = "console"
        arcprint("We are running this script from the Spyder IDE")
    else: 
        arcprint("We are running this script from inside ArcGIS")

    if dist1==dist2:
        #arcerror("The districts must be different. Currently, dist1={0} and dist2={1}.",dist1,dist2)
        arcprint("The districts must be different. Currently, dist1={0} and dist2={1}.",dist1,dist2) #Instead of breaking the system, we return to picking new districts
        arcprint("neighbor_list is {0} and has type {1}",  neighbor_list, type(neighbor_list))
        continue

    dist1=int(dist1)
    dist2=int(dist2)

    [namefields,distfields,nbrlist_fields] = FindNamingFields(neighbor_list)
    NFL = len(namefields) #NFL = Name Field Length (How many fields name the polygons)
    DFL = len(distfields) #DFL = District Fields Length (How many fields denote the district number)

    """arcprint("NFL = {0}", NFL)
    arcprint("DFL = {0}", DFL)"""

## Where Amy's code edits start.
    dist1_bdnds = [] #Creates empty list of boundary units for dist1
    dist2_bdnds = [] #Creates empty list of boundary units for dist2

#Fills list of boundary units for dist1 and dist2
    with arcpy.da.SearchCursor(shapefile, ["OBJECTID", "Cluster_ID"], """{}={} AND ({}={} OR {}={})""".
                           format("Boundary",1, "Cluster_ID", dist1,"Cluster_ID",dist2)) as cursor: #Limits search to rows containing units from dist1 and dist2
        for row in cursor:
            if row[1]==dist1: #If ClusterID==dist1 and Boundary unit is Yes
                if dist1_bdnds.count(row[0])==0: #If we haven't already added the unit, add it to the list
                    dist1_bdnds.append(row[0])
            if row[1]==dist2: #If ClusterID==dist2 and Boundary unit is Yes
                if dist2_bdnds.count(row[0])==0:  #If we haven't already added the unit, add it to the list
                    dist2_bdnds.append(row[1])
    if len(dist1_bdnds)<=len(dist2_bdnds): #Determine the district with the fewest boundary units
        pridist = dist1
        secdist = dist2
    if len(dist1_bdnds)>len(dist2_bdnds):
        pridist = dist2
        secdist = dist1

    AdjFlag = False
    if dist1==pridist:
        dist_tuple = tuple(dist1_bdnds)
    else: 
        dist_tuple = tuple(dist2_bdnds)
    with arcpy.da.SearchCursor(neighbor_list, ["src_OBJECTID", "nbr_OBJECTID"], """({} IN {}) AND {}={}""".
                                   format("src_OBJECTID", dist_tuple,"nbr_CLUSTER_ID",secdist)) as cursor:
        for row in cursor:
            AdjFlag = True
            arcprint("Adjacency Established between districts {0} and {1} by units {2} and {3}", pridist, secdist, row[0],row[1])
            break
    if AdjFlag==False: #Instead of breaking we return back to pick new districts
        arcprint("Districts {0} and {1} are not adjacent.",pridist, secdist)
        continue

## Where Amy's code edits end.

    G = nx.Graph() #Creates an empty graph
    nodes = [] #Creates empty node list
    edges = [] #Creates empty edge list

# Following line requires two-sided neighbor relationship. Maybe fix later.
    with arcpy.da.SearchCursor(neighbor_list, nbrlist_fields, """{}={} OR {}={}""".format(distfields[0], dist1,distfields[0],dist2)) as cursor:
        for row in cursor:
            if nodes.count(row[0])==0:
                nodes.append(row[0]) # If the node is not in the nodes list, add it
                G.add_node(row[0])
            if edges.count([row[0],row[1]])==0 and edges.count([row[1],row[0]])==0 and (row[NFL]==dist1 or row[NFL]==dist2) and (row[NFL+1]==dist1 or row[NFL+1]==dist2):
                edges.append([row[0],row[1]]) #If the edge is not in the edge list AND the both vertices are either dist1 or dist2, add the edge
                G.add_edge(row[0],row[1])


    pop_num={} #Initializes a dictionary that will contain population numbers for each polygon.
#NEED TO MAKE THIS NEXT LINE MORE GENERALIZED. 
    with arcpy.da.SearchCursor(shapefile,["OBJECTID","SUM_Popula","CLUSTER_ID"],"""{}={} OR {}={}""".format("CLUSTER_ID",dist1,"CLUSTER_ID",dist2)) as cursor:
        for row in cursor:
            pop_num[row[0]] = row[1] #For each node, we associate its population

    pop_num=dict(pop_num)
    nx.set_node_attributes(G,pop_num,"Population")       

    arcprint("Edges of G are {0}",G.edges)
    arcprint("Vertices of G are {0}",G.nodes)

    #T = nx.minimum_spanning_tree(G,algorithm='kruskal')
    T = wilson(G,random) #Creates a uniform random spanning tree for G using Wilson's algorithm
    arcprint("T edges are {0}",T.edges)
    nx.set_node_attributes(T,pop_num,"Population") 
    FindEdgeCut(T,30,"Population") #Removes an edge from T so that the Population of each subgraph is within tolerance
    
    IterationCount += 1
    if IterationCount==1:
        StopCriterion = True
