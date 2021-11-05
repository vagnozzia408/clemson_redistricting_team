# -*- coding: utf-8 -*-
"""
Created on Thu Nov  4 14:03:05 2021

@author: blake & amy
"""
import networkx as nx

stateG = nx.Graph()
stateG.add_node("1a")
stateG.add_node("1b")
stateG.add_node("1c")
stateG.add_node("2a")
stateG.add_node("2b")
stateG.add_node("2c")
stateG.add_node("2d")
stateG.add_node("2e")
stateG.add_node("3a")
stateG.add_node("3b")
stateG.add_node("3c")
stateG.add_node("3d")
stateG.add_node("3e")

stateG.nodes["1a"]["District Number"] = 1
stateG.nodes["1b"]["District Number"] = 1
stateG.nodes["1c"]["District Number"] = 1
stateG.nodes["2a"]["District Number"] = 2
stateG.nodes["2b"]["District Number"] = 2
stateG.nodes["2c"]["District Number"] = 2
stateG.nodes["2d"]["District Number"] = 2
stateG.nodes["2e"]["District Number"] = 2
stateG.nodes["3a"]["District Number"] = 3
stateG.nodes["3b"]["District Number"] = 3
stateG.nodes["3c"]["District Number"] = 3
stateG.nodes["3d"]["District Number"] = 3
stateG.nodes["3e"]["District Number"] = 3

stateG.add_edge("1a","1b")
stateG.add_edge("1b","1c")
stateG.add_edge("1b","3a")
stateG.add_edge("1a","2a")
stateG.add_edge("1a","3a")
stateG.add_edge("2a","3a")
stateG.add_edge("2a","2b")
stateG.add_edge("2a","2d")
stateG.add_edge("2b","2e")
stateG.add_edge("2b","2c")
stateG.add_edge("2c","2e")
stateG.add_edge("2c","3c")
stateG.add_edge("2d","3a")
stateG.add_edge("2d","3b")
stateG.add_edge("2d","2e")
stateG.add_edge("2e","3e")
stateG.add_edge("1c","3a")
stateG.add_edge("1c","3d")
stateG.add_edge("3a","3b")
stateG.add_edge("3b","3d")
stateG.add_edge("3b","3e")
stateG.add_edge("3e","3c")

boundarylist = ["1a", "1b", "1c", "2a", "2c", "2d", "2e", "3a", "3b", "3c", "3d", "3e"]
boundarypairs = [("1a","2a"), ("1a","3a"), ("2a","3a"), ("2c","3c"), ("2d","3a"), ("2d","3b"), ("2e","3e"), ("1c","3a"), ("1c","3d"), ("1b","3a")]
src_id = "2e"
cur_dist = 2
new_dist = 3


stateG.nodes[src_id]["District Number"] = new_dist     
connectionsToNewDist = [(p1,p2) for (p1,p2) in boundarypairs if p1 == src_id or p2 == src_id]
for (p1,p2) in connectionsToNewDist:
    if p1 == src_id:
        if stateG.nodes[p2]["District Number"] == new_dist:
            boundarypairs.remove((p1,p2))
    if p2 == src_id:
        if stateG.nodes[p1]["District Number"] == new_dist:
            boundarypairs.remove((p1,p2))
for n in stateG.neighbors(src_id):
    if stateG.nodes[n]["District Number"] == cur_dist: 
        if n not in boundarylist: 
             boundarylist.append(n)
        boundarypairs.append(tuple(sorted((src_id,n))))
    elif stateG.nodes[n]["District Number"] == new_dist: 
        connectionToBoundary = False
        for nn in stateG.neighbors(n):
            if stateG.nodes[nn]["District Number"] != new_dist:
                connectionToBoundary = True
                break
        if connectionToBoundary != True:
            boundarylist.remove(n)    
print(sorted(boundarylist))
print(sorted(boundarypairs))