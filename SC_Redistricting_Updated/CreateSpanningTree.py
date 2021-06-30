# -*- coding: utf-8 -*-
"""
Created on Wed Jun 23 18:21:17 2021

@author: blake

This code is designed to take in a graph G=(V,E) and create a spanning tree on 
the edges on that graph. 
Alternatively, instead of taking in a graph, this code should be designed to
take in a graph G=(V,E) and two adjacent districts. Then a subgraph imposed on 
the nodes of those two districts will be constructed. Thereafter, we will create 
a spanning tree on the resulting subgraph. 
"""

###TO DO: 
"#1. Change asterisk on 'with .... as cursor:' line to include actual field names --- DONE (Blake). "
#2. Validate that districts are adjacent
#3. Figure out how to adjust script validation in ArcGIS Pro so that methodtype changes the rest of the input. 
#4. Edit "with .... as cursor:" line to include more robust SQL statement. 
#5. Currently, this code assumes that our neighbor list include both sides of every edge. Should we build it so that it doesn't necessarily assume that?
"#6. Probably need to hard-code Wilson's algorithm --- DONE (Blake). Taken from Greg's code."
#7. Need to determine how to split the spanning tree into two pieces and recover the two pieces. IDEA: maybe networkx has some functionality that will let it determine which edges are in which tree



import arcpy, os
import random
import networkx as nx

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




currentdir = os.getcwd()
path = currentdir + "\\SC_Redistricting_Updated.gdb"

methodtype = arcpy.GetParameterAsText(0)
neighbor_list=arcpy.GetParameterAsText(1)
dist1=arcpy.GetParameterAsText(2)
dist2=arcpy.GetParameterAsText(3)
shapefile=arcpy.GetParameterAsText(4)

dist1=int(dist1)
dist2=int(dist2)
      
###NEED VALIDATION THAT THE TWO DISTRICTS ACTUALLY TOUCH EACH OTHER

[namefields,distfields,nbrlist_fields] = FindNamingFields(neighbor_list)
NFL = len(namefields) #NFL = Name Field Length (How many fields name the polygons)
DFL = len(distfields) #DFL = District Fields Length (How many fields denote the district number)
arcpy.AddMessage("NFL = {}".format(NFL))
arcpy.AddMessage("DFL = {}".format(DFL))
  
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
            edges.append([row[0],row[1]])
            G.add_edge(row[0],row[1])

arcpy.AddMessage("Edges of G are {}".format(G.edges))
arcpy.AddMessage("Vertices of G are {}".format(G.nodes))

#T = nx.minimum_spanning_tree(G,algorithm='kruskal')
T = wilson(G,random) #Creates a uniform random spanning tree for G. 
arcpy.AddMessage("T edges are {}".format(T.edges))