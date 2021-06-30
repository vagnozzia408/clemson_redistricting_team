import numpy as np
import networkx as nx
import operator

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

def nspanning(graph):
    '''Returns ln(tau(graph)).'''
    L = nx.laplacian_matrix(graph).toarray()
    return np.linalg.slogdet(L[1:,1:])[1]

def findEdgeDistFromRoot(tree, root):
    distFromRoot = {}
    nodeQueue = set([root])
    nodesExamined = set()
    height = 1
    while nodeQueue:
        for node in nodeQueue:
            for edge in tree.edges(node):
                edgeKey = frozenset(edge)
                if edgeKey not in distFromRoot.keys():
                    distFromRoot[frozenset(edge)] = height
        nodesExamined.update(nodeQueue)
        nodeQueue = {newNode for examinedNode in nodeQueue 
                             for newNode in tree.neighbors(examinedNode) 
                             if newNode not in nodesExamined}
        height += 1
    return distFromRoot

def findEdgeCutWeights(root, tree, treePop, distFromRoot, state, info, 
                       boolop = operator.and_):
    graph = state["graph"]
    sortedEdges = sorted(tree.edges, key=lambda e:distFromRoot[frozenset(e)], 
                         reverse=True)
    #weights (find good edge sets)
    edgeWeights = {}
    possibleEdgeCuts = set()
    for edge in sortedEdges:
        edgeKey = frozenset(edge)
        maxNbrHeight = max(distFromRoot[frozenset(eKey2)] 
                           for eKey2 in tree.edges(list(edge)))
        leafEdge_huh = distFromRoot[edgeKey] == maxNbrHeight

        if root in edgeKey and tree.degree(root) == 1:
            leafEdge_huh = False
        
        if leafEdge_huh:
            leafNode = [n for n in edge if tree.degree(n) == 1][0]
            edgeWeights[edgeKey] = graph.nodes[leafNode]["Population"]
            pop = edgeWeights[edgeKey]
            if boolop(state["minPop"] <= pop <= state["maxPop"],
                      state["minPop"] <= treePop - pop <= state["maxPop"]):
                possibleEdgeCuts.add(edgekey)
        else:
            edgeWeights[edgeKey] = 0
            for edgeNbr in tree.edges(list(edge)):
                eNbrKey = frozenset(edgeNbr)
                if distFromRoot[eNbrKey] > distFromRoot[edgeKey]:
                    edgeWeights[edgeKey] += edgeWeights[eNbrKey]
                    awayNode = list(eNbrKey.intersection(edgeKey))[0]
            try:
                edgeWeights[edgeKey] += graph.nodes[awayNode]["Population"]
            except:
                # only way to fail is if the root is the leaf and t
                awayNode = list(edgeKey - set([root]))[0]
                edgeWeights[edgeKey] += graph.nodes[awayNode]["Population"]

            pop = edgeWeights[edgeKey]
            if boolop(state["minPop"] <= pop <= state["maxPop"],
                      state["minPop"] <= treePop - pop <= state["maxPop"]) :
                possibleEdgeCuts.add(edgeKey)
    return possibleEdgeCuts, edgeWeights
    
def edgeCuts(tree, treePop, state, info, boolop = operator.and_, 
             retRoot = False):
    '''Returns the set of good edges and the weights of edges'''
    root = list(tree.nodes)[0] #arbitrary choice of root

    distFromRoot = findEdgeDistFromRoot(tree, root)
    possibleEdgeCuts, edgeWeights = findEdgeCutWeights(root, tree, 
                                                       treePop, distFromRoot,
                                                       state, info, boolop)
    if not retRoot:
        return possibleEdgeCuts, edgeWeights
    else:
        return possibleEdgeCuts, edgeWeights, root
    

def findNodeDistFromRoot(root, edgeWeights):
    nodeToRootDist = {root: 0}
    tmpTree = nx.Graph()
    tmpTree.add_edges_from(edgeWeights.keys())

    queue = set([root])
    visted = set([])
    while len(queue) > 0:
        newQueue = set([])
        for node in queue:
            visted.add(str(node))
        for node in queue:
            for nbrNode in tmpTree.neighbors(node):
                if nbrNode not in visted:
                    nodeToRootDist[nbrNode] = nodeToRootDist[node] + 1
                    newQueue.add(nbrNode)
        queue = newQueue
    return nodeToRootDist

def countEdgeCutsFromNode(cutTree, cutTreePop, treePop, node, nodeToRootDist, 
                          edgeWeights, state):

    queue = set([node])
    visited = set([])

    edgesToCut = 0

    while len(queue) > 0:
        newQueue = set([])
        for node in queue:
            visited.add(node)
        for node in queue:
            for nbrNode in cutTree.neighbors(node):
                if nbrNode in visited:
                    continue
                toRoot = (nodeToRootDist[node] - nodeToRootDist[nbrNode]) > 0
                edgeKey = frozenset((node, nbrNode))
                edgePop = edgeWeights[edgeKey]
                if toRoot:
                    popA = edgePop + (treePop - cutTreePop)
                    popB = cutTreePop - edgePop
                else:
                    popA = edgePop
                    popB = treePop - edgePop

                if state["minPop"] <= popA <= state["maxPop"] and \
                   state["minPop"] <= popB <= state["maxPop"]:
                   edgesToCut += 1
                   newQueue.add(nbrNode)
        queue = newQueue
    return edgesToCut


def countEdgeCuts(cutTree, treePop, state, info, borderEdges, edgeJoinCounts):

    graph = state["graph"]
    cutTreePop = sum([graph.nodes[n]["Population"] for n in cutTree])
    cut, edgeWeights, root = edgeCuts(cutTree, cutTreePop, state, info, 
                                      retRoot = True)
    nodeToRootDist = findNodeDistFromRoot(root, edgeWeights)
    
    for edge in borderEdges:
        node = [n for n in edge if n in cutTree][0]
        totCutEdges = countEdgeCutsFromNode(cutTree, cutTreePop, treePop, node, 
                                            nodeToRootDist, edgeWeights, state)
        edgeJoinCounts[edge] += totCutEdges


def crossEdgeProbSum(tree1, tree2, treePop, borderEdges, state, info):
    '''Returns the sum of probabilities that the trees are is split into tree1 
       and tree2, given any possible connecting edge on the graph of state
       '''
    edgeJoinCounts = {e:1 for e in borderEdges}

    countEdgeCuts(tree1, treePop, state, info, borderEdges, edgeJoinCounts)
    countEdgeCuts(tree2, treePop, state, info, borderEdges, edgeJoinCounts)
    
    return sum(1/float(x) for x in edgeJoinCounts.values())
