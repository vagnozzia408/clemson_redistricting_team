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
#1. Change asterisk on "with .... as cursor:" line to include actual field names
#2. Validate that districts are adjacent
#3. Figure out how to adjust script validation in ArcGIS Pro so that methodtype changes the rest of the input. 
#4. Edit "with .... as cursor:" line to include more robust SQL statement. 
#5. Currently, this code assumes that our neighbor list include both sides of every edge. Should we build it so that it doesn't necessarily assume that?
#6. Probably need to hard-code Wilson's algorithm
#7. Need to determine how to split the spanning tree into two pieces and recovery the two pieces. IDEA: maybe networkx has some functionality that will let it determine which edges are in which tree



import arcpy, os
import networkx as nx

currentdir = os.getcwd()
path = currentdir + "\\SC_Redistricting_Updated.gdb"

methodtype = arcpy.GetParameterAsText(0)
neighbor_list=arcpy.GetParameterAsText(1)
dist1=arcpy.GetParameterAsText(2)
dist2=arcpy.GetParameterAsText(3)

dist1=int(dist1)
dist2=int(dist2)

if 1==0: # Skipping for now ####FIX LATER. SHOULD ACCOUNT FOR METHODTYPE
    G = nx.Graph() #Creates an empty graph
    nodes = [] #Creates empty node list
    edges = [] #Creates empty edge list
    
    with arcpy.da.SearchCursor(neighbor_list, "*") as cursor:
        for row in cursor:
    #        arcpy.AddMessage("Col 0 is {0}. Col 1 is {1}. Col 2 is {2},".format(row[0],row[1],row[2]))
            if nodes.count(row[1])==0:
                nodes.append(row[1]) # If the node is not in the nodes list, add it
                G.add_node(row[1])
            if edges.count([row[1],row[2]])==0 and edges.count([row[2],row[1]])==0:
                edges.append([row[1],row[2]]) # If the edge (or backwards edge) is not in the edges list, add it
                G.add_edge(row[1],row[2])
    
    T = nx.minimum_spanning_tree(G, algorithm='kruskal')
    arcpy.AddMessage("T edges are {}".format(T.edges))
        
###NEED VALIDATION THAT THE TWO DISTRICTS ACTUALLY TOUCH EACH OTHER
    
G = nx.Graph() #Creates an empty graph
nodes = [] #Creates empty node list
edges = [] #Creates empty edge list


with arcpy.da.SearchCursor(neighbor_list, "*", """{}={} OR {}={}""".format("src_CLUSTER_ID", dist1,"src_CLUSTER_ID",dist2)) as cursor:
    for row in cursor:
        if nodes.count(row[1])==0:
            nodes.append(row[1]) # If the node is not in the nodes list, add it
            G.add_node(row[1])
        if edges.count([row[1],row[2]])==0 and edges.count([row[2],row[1]])==0 and (row[3]==dist1 or row[3]==dist2) and (row[4]==dist1 or row[4]==dist2):
            edges.append([row[1],row[2]])
            G.add_edge(row[1],row[2])

T = nx.minimum_spanning_tree(G,algorithm='kruskal')
arcpy.AddMessage("T edges are {}".format(T.edges))