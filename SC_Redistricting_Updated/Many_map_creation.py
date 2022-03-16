# -*- coding: utf-8 -*-
"""
Created on Sun Mar 8 21:10:00 2022

@author: Blake Splitter
"""

from decimal import DivisionByZero
from copy import deepcopy
from multiprocessing.sharedctypes import Value
import sys
import os
import arcpy
import datetime
import random
from inspect import signature
import networkx as nx
import numpy as np
import math
import pandas as pd
import statistics


class input:
    def __init__(self, dc, in_table, mc, in_n_f, in_p_f, in_vb_f, in_vr_f, in_c_f):
        self.distcount = dc
        self.in_table = in_table
        self.maps_created = mc
        self.in_name_field = in_n_f
        self.in_pop_field = in_p_f
        self.in_voteblue_field = in_vb_f
        self.in_votered_field = in_vr_f
        self.in_county_field = in_c_f
        self.total_obj_vals_entries = 1


class objective_vals:

    def __init__(self, ip):
        self.dev_vals = [0] * ip.total_obj_vals_entries
        self.avg_comp_vals = [0] * ip.total_obj_vals_entries
        self.eg_score_vals = [0] * ip.total_obj_vals_entries
        self.CDI_Count_vals = [0] * ip.total_obj_vals_entries
        self.excess_GU_vals = [0] * ip.total_obj_vals_entries
        self.mm_vals = [0] * ip.total_obj_vals_entries
        self.change_type_vals = [None] * ip.total_obj_vals_entries
        self.dev_recom_change = [0] * ip.total_obj_vals_entries
        self.avg_comp_recom_change = [0] * ip.total_obj_vals_entries
        self.eg_score_recom_change = [0] * ip.total_obj_vals_entries
        self.CDI_Count_recom_change = [0] * ip.total_obj_vals_entries
        self.excess_GU_recom_change = [0] * ip.total_obj_vals_entries
        self.mm_recom_change = [0] * ip.total_obj_vals_entries

    def fill_obj_vals(self, dev, comp, eg, cdi_data, mm, change, it, ip):
        self.dev_vals[it] = dev
        self.avg_comp_vals[it] = comp
        self.eg_score_vals[it] = eg
        self.CDI_Count_vals[it] = cdi_data.cdi_count
        self.excess_GU_vals[it] = cdi_data.excess_GU
        self.mm_vals[it] = mm
        self.change_type_vals[it] = change

        if change == "recom":  #Finds the change in each objective value since the last recom or failed recom
            self.dev_recom_change[it] = self.dev_vals[it] - self.dev_vals[it - ip.num_flips - 1]
            self.avg_comp_recom_change[it] = self.avg_comp_vals[it] - self.avg_comp_vals[it - ip.num_flips - 1]
            self.eg_score_recom_change[it] = self.eg_score_vals[it] - self.eg_score_vals[it - ip.num_flips - 1]
            self.CDI_Count_recom_change[it] = self.CDI_Count_vals[it] - self.CDI_Count_vals[it - ip.num_flips - 1]
            self.excess_GU_recom_change[it] = self.excess_GU_vals[it] - self.excess_GU_vals[it - ip.num_flips - 1]
            self.mm_recom_change[it] = self.mm_vals[it] - self.mm_vals[it - ip.num_flips - 1]
        else:
            self.dev_recom_change[it] = None
            self.avg_comp_recom_change[it] = None
            self.eg_score_recom_change[it] = None
            self.CDI_Count_recom_change[it] = None
            self.excess_GU_recom_change[it] = None
            self.mm_recom_change[it] = None

    @property
    def avg_dev_change(self):
        """Finds the average change in deviation between recom steps"""
        return sum(filter(lambda i: isinstance(i, (int, float)), self.dev_recom_change))

    @property
    def avg_comp_change(self):
        """Finds the average change in compactness between recom steps"""
        return sum(filter(lambda i: isinstance(i, (int, float)), self.avg_comp_recom_change))

    @property
    def avg_eg_change(self):
        """Finds the average change in efficiency gap score between recom steps"""
        return sum(filter(lambda i: isinstance(i, (int, float)), self.eg_score_recom_change))

    @property
    def avg_CDI_Count_change(self):
        """Finds the average change in CDI Count between recom steps"""
        return sum(filter(lambda i: isinstance(i, (int, float)), self.CDI_Count_recom_change))

    @property
    def avg_excess_GU_change(self):
        """Finds the average change in excess GUs between recom steps"""
        return sum(filter(lambda i: isinstance(i, (int, float)), self.excess_GU_recom_change))

    @property
    def avg_mm_change(self):
        """Finds the average change in median mean between recom steps"""
        return sum(filter(lambda i: isinstance(i, (int, float)), self.mm_recom_change))

    def __repr__(self):
        last_it = np.max(np.nonzero(self.dev_vals))
        dev = self.dev_vals[last_it]
        eg = self.eg_score_vals[last_it]
        cdi = self.CDI_Count_vals[last_it]
        eGU = self.excess_GU_vals[last_it]
        ct = self.change_type_vals[last_it]
        mm = self.mm_vals[last_it]
        return "{0} iterations filled. Last entry: deviation = {1}, eg = {2}, cdi_count = {3}, excess_GU = {4}, mm = {5}, change_type = {6}".format(last_it, dev, eg, cdi, eGU, mm, ct)


class District:
    """A class that will hold the statistics associated with each district"""
    ideal_pop = 0  #The ideal population that a district would like to be
    num_dists = 0  #The number of districts
    
    def __init__(self, num):
        self.num = num  #District numbers will range from 1 to n
        self.Area = None  #Area in units of square kilometers
        self.Perimeter = None  #Perimeter in units of kilometers
        self.HypArea = None  #Hypothetical area after a proposed change
        self.HypPerimeter = None  #Hypothetical perimeter after a proposed change
        self.VoteCountRed = None  #Red votes in a district
        self.VoteCountBlue = None  #Blue votes in a district
        self.HypVoteCountRed = None  #Hypothetical red vote count after a proposed change
        self.HypVoteCountBlue = None  #Hypothetical blue vote count after a proposed change
        self.Population = None  #Population of the district
        self.Dist_nbrs = []  #Set of district neighbors

    def __repr__(self):
        return "District Number {0}. Population: {1}. Area: {2} km^2. Perimeter: {3} km. PP Score: {4}. Ideal population target: {5}.".format(self.num, self.Population, self.Area, self.Perimeter, self.PPCompactScore, self.ideal_pop)

    @property
    def PPCompactScore(self):
        '''Polsby-Popper Compactness Score (ranges from 0 to 1; 1 is best)'''
        try: 
            return 4 * math.pi * self.Area / self.Perimeter ** 2 if self.Perimeter != 0 else None
        except TypeError:
            return None

    @property
    def invPPCompactScore(self):
        '''Returns the inverse of the Polsby-Popper Compactness Score and subtracts 1 so that the ideal score is 0'''
        return (1 / self.PPCompactScore) - 1 if self.PPCompactScore != 0 and self.PPCompactScore != None else None

    @property
    def HypPPCompactScore(self):
        '''Hypothetical Polsby-Popper Compactness after a proposed change'''
        try: 
            return 4 * math.pi * self.HypArea / self.HypPerimeter ** 2 if self.HypPerimeter != 0 else None
        except TypeError:
            return None

    @property
    def TotalVotes(self):
        '''Sums red votes and blue votes for a district'''
        try:
            return self.VoteCountBlue + self.VoteCountRed
        except TypeError:
            return None

    @property
    def HypTotalVotes(self):
        '''Sums hypothetical red votes and hypothetical blue votes for a district'''
        try:
            return self.HypVoteCountBlue + self.HypVoteCountRed
        except TypeError:
            return None

    @property
    def BlueShare(self):
        '''Returns the share of blue votes as a proportion of total votes'''
        try:
            return self.VoteCountBlue / self.TotalVotes if self.TotalVotes != 0 else None
        except TypeError:
            return None

    @property
    def HypBlueShare(self):
        '''Returns the share of hypothetical blue votes as a proportion of the hypothetical total votes'''
        try:
            return self.HypVoteCountBlue / self.HypTotalVotes if self.HypTotalVotes != 0 else None
        except TypeError:
            return None

    @property
    def EfficiencyGap(self):
        '''Returns the Efficiency gap as calculated by (wastedRed votes - wastedBlue votes) / total votes'''
        try:
            return (self.WastedRed - self.WastedBlue) / self.TotalVotes if self.TotalVotes != 0 else None
        except TypeError:
            return None

    @property
    def AbsEfficiencyGap(self):
        '''Returns the absolute value of the efficiency gap'''
        try:
            return abs(self.EfficiencyGap)
        except TypeError:
            return None

    @property
    def HypEfficiencyGap(self):
        '''Returns the Hypothetical Efficiency gap as calculated by (wastedRed votes - wastedBlue votes) / total votes'''
        try:
            return (self.HypWastedRed - self.HypWastedBlue) / self.HypTotalVotes if self.HypTotalVotes != 0 else None
        except TypeError:
            return None

    @property
    def WinThreshold(self):
        '''Returns the number of votes needed to win an election in a district'''
        try:
            return math.ceil(self.TotalVotes / 2 + 0.5)  #The '+0.5' is needed to deal with cases where the total number of votes is even
        except TypeError:
            return None

    @property
    def HypWinThreshold(self):
        '''Returns the number of hypothetical votes needed to win an election in a district'''
        try: 
            return math.ceil(self.HypTotalVotes / 2 + 0.5)  #The '+0.5' is needed to deal with cases where the total number of votes is even
        except TypeError:
            return None

    @property
    def WastedBlue(self):
        '''Returns the number of wasted blue votes. If the blue party wins, then this value will be 
        the number of blue votes beyond the win threshold. If the blue party loses, then this will be the
        number of blue votes. For coding simplicity, all ties are won by the blue party.'''
        try:
            if self.VoteCountBlue >= self.VoteCountRed:
                return self.VoteCountBlue - self.WinThreshold
            else:
                return self.VoteCountBlue
        except TypeError:
            return None

    @property
    def WastedRed(self):
        '''Returns the number of wasted red votes. If the red party wins, then this value will be 
        the number of red votes beyond the win threshold. If the red party loses, then this will be the
        number of red votes. For coding simplicity, all ties are won by the blue party.'''
        try:
            if self.VoteCountRed >= self.VoteCountBlue:
                return self.VoteCountRed - self.WinThreshold
            else:
                return self.VoteCountRed
        except TypeError:
            return None

    @property
    def HypWastedBlue(self):
        '''Returns the number of wasted blue votes after a proposed change. If the blue party wins, then this value will be 
        the number of hypothetical blue votes beyond the win threshold. If the blue party loses, then this will be the
        number of hypothetical blue votes. For coding simplicity, all ties are won by the blue party.'''
        try:
            if self.HypVoteCountBlue >= self.HypVoteCountRed:
                return self.HypVoteCountBlue - self.HypWinThreshold
            else:
                return self.HypVoteCountBlue
        except TypeError:
            return None

    @property
    def HypWastedRed(self):
        '''Returns the number of wasted red votes after a proposed change. If the red party wins, then this value will be 
        the number of hypothetical red votes beyond the win threshold. If the red party loses, then this will be the
        number of hypothetical red votes. For coding simplicity, all ties are won by the blue party.'''
        try:
            if self.HypVoteCountRed >= self.HypVoteCountBlue:
                return self.HypVoteCountRed - self.HypWinThreshold
            else:
                return self.HypVoteCountRed
        except TypeError:
            return None
    
    def UpdateStats(self, a, p, vcr, vcb):
        self.Area = a
        self.Perimeter = p
        self.VoteCountRed = vcr
        self.VoteCountBlue = vcb
    
    def UpdateCompStats(self, a, p):
        self.Area = a
        self.Perimeter = p
        
    def UpdateHypStats(self, a, p):
        self.HypArea = a
        self.HypPerimeter = p
        
    def ConfirmStats(self, status):
        if status == True:
            self.UpdateStats(self.HypArea, self.HypPerimeter, self.HypVoteCountRed, self.HypVoteCountBlue)
        self.HypArea = 0
        self.HypPerimeter = 0
        self.HypVoteCountRed = 0
        self.HypVoteCountBlue = 0

    @staticmethod
    def pop_list(dist_list):
        '''Returns a list of populations for each district'''
        pop_list = [d.Population for d in dist_list]
        pop_list = remove_nones(pop_list)
        return pop_list

    @staticmethod
    def EG_list(dist_list, AV=False):
        '''Returns a list of efficiency gaps for each district. If AV is true, then we return the absolute values'''
        if AV == False:
            eg_list = [d.EfficiencyGap for d in dist_list]
        else: 
            eg_list = [d.AbsEfficiencyGap for d in dist_list]
        
        eg_list = remove_nones(eg_list)        
        return eg_list

    @staticmethod
    def blue_share_list(dist_list):
        '''Returns a list of blue proportions of votes (as a fraction of total votes in district) for each district.'''
        bs_list = [d.BlueShare for d in dist_list]
        bs_list = remove_nones(bs_list)
        return bs_list


    def reset_vals(self):
        '''Resets several values. Useful during recom'''
        self.Area = 0
        self.Perimeter = 0
        self.VoteCountRed = 0
        self.VoteCountBlue = 0
        self.Population = 0
        self.Dist_nbrs = []


class CDI:
    """A class that will contain all information about the county-district-intersection matrix"""
    def __init__(self, stateG):
        distcount = len(set(dict(stateG.nodes("District Number")).values()))  #Finds number of unique districts
        num_counties = len(set(dict(stateG.nodes("County Number")).values()))  #Finds number of unique counties
        units_in_CDI = np.zeros([distcount, num_counties], dtype=int)
    
        # #Adds 1 to the matrix element A[i,j] if there is a precinct in the ith district and jth county
        for n in stateG:
            if stateG.nodes[n]["District Number"] == 0:
                continue
            else:
                units_in_CDI[stateG.nodes[n]["District Number"] - 1][stateG.nodes[n]["County Number"] - 1] += 1

        self.cdi_mat = units_in_CDI
        self.distcount = distcount
        self.num_counties = num_counties
    
    @property
    def cdi_count(self):
        '''Counts number of nonzero entries in the CDI matrix. Then subtracts either the distcount or number of counties, so that the ideal value will be zero.'''
        return np.count_nonzero(self.cdi_mat) - max(self.distcount, self.num_counties)
    
    @property
    def excess_GU(self):
        '''GU stands for Geographical Unit. In this loop, we count the number of GUs in each county that are not in the most prevalent district. The ideal number of excess GUs is zero.'''
        excess_GU_mat = [0] * max(self.distcount, self.num_counties)
        transpose = self.cdi_mat.transpose()
        idx = 0
        for row in transpose:
            maxval = max(row)
            excess_GU_mat[idx] = sum(row) - maxval
            idx += 1
        return sum(excess_GU_mat)
    
    def upd_cdi_mat_flip(self, stateG, GU, leaving_dist, entering_dist):
        '''Updates the cdi matrix after a flip'''
        self.cdi_mat[leaving_dist - 1][stateG.nodes[GU]["County Number"] - 1] -= 1
        self.cdi_mat[entering_dist - 1][stateG.nodes[GU]["County Number"] - 1] += 1


class counters:
    '''A class that will contain the counters used in the simulated annealing step'''
    def __init__(self):
        self.flipcount = 0  #The number of flips done in total in the code
        self.recomcount = 0  #The number of recombination steps done in total in the code
        self.stopcounter = 0  #The number of consecutive failed recombination steps in the current iteration
        self.alphacount = 0  #The number of alpha values utilized previously
        self.its_at_temp = 0  #The number of iterations that have occurred at this temperature

    @property
    def currentit(self):
        '''Returns the sum of the flip count and the recom count'''
        return self.flipcount + self.recomcount  #This returns the index that will be populated in obj_vals

    def __repr__(self):
        return "flipcount = {0}. recomcount = {1}. stopcounter = {2}. currentit = {3}".format(self.flipcount, self.recomcount, self.stopcounter, self.currentit)


class Map_class:
    """A class that will contain a graph and its associated metric values"""
    def __init__(self, graph, alpha, dist_list, cdi_data):
        self.graph = graph
        self.alpha = alpha
        self.dist_list = dist_list
        self.cdi_data = cdi_data

    @property
    def pop_dev(self):
        """Calculates population deviation for this map"""
        return pop_deviation(self.dist_list)
    
    @property
    def compactness(self):
        """Calculates Inverse Polsby-Popper compactness (minus 1) for this map"""
        return comp_score(self.dist_list)

    @property
    def eg(self):
        """Calculates efficiency gap score for this map"""
        return eg_score(self.dist_list)

    @property
    def cdi_num(self):
        """Calculates the number of county-district intersections for this map"""
        return self.cdi_data.cdi_count

    @property    
    def excess_GU_num(self):
        """Calculates the number of excess GUs for this map"""
        return self.cdi_data.excess_GU

    @property
    def mm(self):
        """Calculates the median-mean score for the map"""
        return median_mean(self.dist_list)


    def compare_objs(self, pareto_set):
        """Compares the current map with all maps in the pareto set to determine if 
        1. The current map dominates at least one map in the pareto set
        2. The current map is dominated by at least one map in the pareto set
        3. The current map neither dominates nor is dominated by any map in the pareto set
        """
        nonequal_flag = False
        random.shuffle(pareto_set)
        for Map in pareto_set:
            if self.pop_dev == Map.pop_dev and self.compactness == Map.compactness and self.eg == Map.eg and self.cdi_num == Map.cdi_num and self.excess_GU_num == Map.excess_GU_num:
                #This is the case where all metrics are equal. May occur if we compare self to self
                continue
            elif self.pop_dev >= Map.pop_dev and self.compactness >= Map.compactness and self.eg >= Map.eg and self.cdi_num >= Map.cdi_num and self.excess_GU_num >= Map.excess_GU_num:
                #This is the case where self is dominated
                return -1, Map
            elif self.pop_dev <= Map.pop_dev and self.compactness <= Map.compactness and self.eg <= Map.eg and self.cdi_num <= Map.cdi_num and self.excess_GU_num <= Map.excess_GU_num:
                #This is the case where self dominates
                return 1, Map
            else:
                #This is the case where self neither dominates nor is dominated. 
                #We need to check all maps, so we pass here
                nonequal_flag = True  #signifies that at least one different map is in the Pareto set
                pass
        if nonequal_flag == False:
            return -2, -2  #Returns -2, -2 if the maps in the Pareto set all are exactly the same as self (this shouldn't happen)
        else:
            return 0, 0  #Returns 0, 0 if self is not dominated by any map and self does not dominate any map


def norm(vector):
    """Input is a list of nonnegative numbers. Returns a normed vector, i.e. a vector that sums to 1."""
    if any(t < 0 for t in vector):
        raise ValueError("All entries in this vector must be nonnegative.")
    tot = sum(vector)
    for i in range(len(vector)):
        vector[i] = vector[i] / tot
    eps = 0.000001
    if sum(vector) > 1 + eps or sum(vector) < 1 - eps:
        raise ValueError("The elements of this vector must sum to 1. Something is wrong with the norm method.")
    return vector


def remove_nones(val_list):
    """Removes all 'None' entries from a list"""
    while True:
        try:
            val_list.remove(None)  #Removes None values from list
        except ValueError:
            break 
    return val_list


def make_county_dict(ip, out_table):
    '''Populates county_dict with 1-x, based on the sorted county numbers'''
    county_list = [row.getValue (ip.in_county_field) for row in arcpy.SearchCursor (out_table["name"])]  #Gets original county values
    county_list = list(map(int, county_list))  #Converts strings to integers
    county_list = sorted(list(set(county_list)))  #Sorts the list and deletes duplicate values
    county_dict = {}
    i = 1
    for county in county_list:
        county_dict[county] = i  #Populates a dictionary that associates each original county value with its sorted value
        i += 1
    return county_dict


def create_buffer_dist(out_table):
    '''Creates a dummy GU that surrounds the state Assigns this dummy GU a district value of 0.'''
    buffer_fc = out_table["name"] + "_Buffer"
    arcpy.Buffer_analysis(out_table["name"], buffer_fc, "1 Kilometers", line_side="OUTSIDE_ONLY", dissolve_option="ALL")
    arcpy.Append_management(buffer_fc, out_table["name"], schema_type="NO_TEST")  #Adds the newly created buffer to the out_table
    row_count = int(arcpy.GetCount_management(out_table["name"]).getOutput(0)) #getOutput(0) returns the value at the first index position of a tool.
    sql_statement = """{} = {}""".format(arcpy.AddFieldDelimiters(out_table["name"], "OBJECTID"), row_count)
    with arcpy.da.UpdateCursor(out_table["name"], out_table["dist_field"], sql_statement) as cursor: #Selects only the last row of the table
        for row in cursor: 
            row[0] = 0  #Dist_Assign = 0
            cursor.updateRow(row)
        del cursor, row

    arcpy.management.Delete(buffer_fc)  #Deletes the buffer feature class


def CreateNeighborList(out_table):
    '''Creates a neighbor list for out_table and deletes all single-point adjacencies'''
    neighbor_list = out_table["name"] + "_nbr_list"
    arcpy.PolygonNeighbors_analysis(out_table["name"], neighbor_list, ["OBJECTID", "CLUSTER_ID"], None, None, None, "KILOMETERS")

    print("Deleting all rows from neighbor list with single-point adjacencies...")
    with arcpy.da.UpdateCursor(neighbor_list, ["NODE_COUNT", "OBJECTID"]) as cursor:
        for row in cursor:
            if row[0] > 0:
                cursor.deleteRow()  #Deletes all rows with that have single-point adjacency
        cursor.reset()  #Resets the cursor back to the first row
        i = 1
        for row in cursor:
            row[1] = i  #Relabels the OBJECTID with its row number (several rows were deleted above)
            i = i + 1
        del cursor

    return neighbor_list


def update_nbr_list(neighbor_list):
    '''Initializes neighbor_list so that each entry in src_dist and nbr_dist is reset to match original districts'''
    if not arcpy.ListFields(neighbor_list, "src_dist"):  #Adds src_dist and nbr_dist to neighbor_list if they don't already exist. These fields will be the ones that change mid-algorithm
        arcpy.AddField_management(neighbor_list, "src_dist", "SHORT", field_alias="Source District")
        arcpy.AddField_management(neighbor_list, "nbr_dist", "SHORT", field_alias="Neighbor District")
    orig_dist_names = []
    lstFields = arcpy.ListFields(neighbor_list)
    for field in lstFields:
        if field.name in ["src_CLUSTER_ID", "src_ZONE_ID", "nbr_CLUSTER_ID", "nbr_ZONE_ID"]:
            orig_dist_names.append(field.name)
    odn = orig_dist_names  #An alias

    #Copies all original district numbers into src_dist and nbr_dist
    #Note: odn[0] = "src_CLUSTER_ID" and odn[1] = "nbr_CLUSTER_ID"
    with arcpy.da.UpdateCursor(neighbor_list, [odn[0], odn[1], 'src_dist', 'nbr_dist']) as cursor:
        for row in cursor:
            row[2] = row[0]  #src_dist = src_CLUSTER_ID
            row[3] = row[1]  #nbr_dist = nrb_CLUSTER_ID
            cursor.updateRow(row)
        del cursor


def build_adj_graph(out_table, nbr_list, ip):
    '''Builds the adjacency graph for all GUs using adjacencies found from neighbor_list'''

    stateG = nx.Graph()  #Creates an empty graph that will contain adjacencies for the entire state
    origdist = {}  #Initializes a dictionary that will contain the original district number for each GU
    distnum = {}  #Initializes a dictionary that will contain the district number for each GU
    popnum = {}  #Initializes a dictionary that will contain the population for each GU
    countynum = {}  #Initializes a dictionary that will contain the county number for each GU
    area = {}  #Initializes a dictionary that will contain the area value for each GU (in square km)
    length = {}  #Initializes a dictionary that will contain each edge length (in km)
    boundary = {}  #Initializes a dictionary that will describe each edge as being a boundary edge or not
    blue_votes = {}  #Initializes a dictionary that will contain the number of blue votes
    red_votes = {}  #Initializes a dictionary that will contain the number of red votes
    sf_name_field = ip.in_name_field
    sf_pop_field = ip.in_pop_field

    print("Creating the adjacency graph for all Geographical Units...")
    print("Adding nodes to stateG...")
    with arcpy.da.SearchCursor(out_table["name"], [sf_name_field, sf_pop_field, out_table["county_field"], out_table["dist_field"], "Area_sq_km", ip.in_voteblue_field, ip.in_votered_field]) as cursor:
        for row in cursor:
            if (row[0] == None or row[1] == None or row[2] == None or row[3] == None or row[4] == None or row[5] == None or row[6] == None) and row[0] != 2261: 
                raise ValueError("An element was None")
            popnum[row[0]] = row[1]  #Finds population of each GU
            countynum[row[0]] = row[2]  #Finds county number for each GU
            origdist[row[0]] = row[3]  #Finds original district number for each GU
            distnum[row[0]] = row[3]  #Finds district number for each GU. 
            area[row[0]] = row[4]  #Finds the area for each GU
            blue_votes[row[0]] = row[5]  #Finds number of blue votes for each GU
            red_votes[row[0]] = row[6]  #Finds number of red votes for each GU
            stateG.add_node(row[0])  #Adds each GU to the node list for stateG
            del row
        del cursor

    print("Adding edges to stateG...")
    with arcpy.da.SearchCursor(nbr_list, ["src_OBJECTID", "nbr_OBJECTID", "src_dist", "nbr_dist", "OBJECTID", "LENGTH"]) as cursor:
        for row in cursor:
            stateG.add_edge(row[0], row[1])
            length[(row[0], row[1])] = float(row[5])
            if row[2] != row[3]:
                if row[2] == 0 or row[3] == 0:  
                    boundary[(row[0], row[1])] = 2  #If either GU is the dummy district
                else:
                    boundary[(row[0], row[1])] = 1  #If edge represents a district boundary
            else: 
                boundary[(row[0], row[1])] = 0  #If edge is not a district boundary
        del cursor

    print("Adding Population attribute")
    nx.set_node_attributes(stateG, popnum, "Population")
    print("Adding District Number attribute")
    nx.set_node_attributes(stateG, distnum, "District Number")
    print("Adding Original District Number attribute")
    nx.set_node_attributes(stateG, origdist, "Original District Number")
    print("Adding County Number attribute")
    nx.set_node_attributes(stateG, countynum, "County Number")
    print("Adding Area attribute")
    nx.set_node_attributes(stateG, area, "Area")
    print("Adding Blue Vote attribute")
    nx.set_node_attributes(stateG, blue_votes, "Blue Votes")
    print("Adding Red Vote attribute")
    nx.set_node_attributes(stateG, red_votes, "Red Votes")
    print("Adding Length attribute for edges")
    nx.set_edge_attributes(stateG, length, "Length")
    print("Adding Boundary status attribute for edges")
    nx.set_edge_attributes(stateG, boundary, "Boundary")
    return stateG


def populate_dist_list(stateG, dist_list):
    '''Populates dist_list with all statistics based on the stateG graph'''
    distcount = len(set(dict(stateG.nodes("District Number")).values()))  #Finds number of unique districts (includes dummy district)
    for i in range(distcount):
        dist_list[i] = District(i)  #Reinitializes (and therefore resets) the dist_list

    for n in stateG.nodes:
        if stateG.nodes[n]["District Number"] == 0:  #Skips dummy district
            continue
        else:
            dist_num = stateG.nodes[n]["District Number"]
            if dist_list[dist_num].Area == None:
                dist_list[dist_num].Area = 0
            if dist_list[dist_num].Population == None:
                dist_list[dist_num].Population = 0
            if dist_list[dist_num].VoteCountBlue == None:
                dist_list[dist_num].VoteCountBlue = 0
            if dist_list[dist_num].VoteCountRed == None:
                dist_list[dist_num].VoteCountRed = 0

            dist_list[dist_num].Area += stateG.nodes[n]["Area"]
            dist_list[dist_num].Population += stateG.nodes[n]["Population"]
            dist_list[dist_num].VoteCountBlue += stateG.nodes[n]["Blue Votes"]
            dist_list[dist_num].VoteCountRed += stateG.nodes[n]["Red Votes"]


    dist_list[0].Population = None
    ideal_pop = round(sum(District.pop_list(dist_list)) / (distcount - 1))  #The -1 excludes the dummy district
    District.ideal_pop = ideal_pop
    District.num_dists = distcount - 1

    print("The starting population of each district is {0}. Thus, the ideal population for a district is {1}.".format( District.pop_list(dist_list), ideal_pop))

    for d in dist_list:
        if d.Perimeter == None:
            d.Perimeter = 0

    for e in list(stateG.edges):
        if stateG[e[0]][e[1]]["Boundary"] == 1 or stateG[e[0]][e[1]]["Boundary"] == 2:
            dist_num0 = stateG.nodes[e[0]]["District Number"]
            dist_num1 = stateG.nodes[e[1]]["District Number"]

            dist_list[dist_num0].Perimeter += stateG[e[0]][e[1]]["Length"]
            dist_list[dist_num1].Perimeter += stateG[e[0]][e[1]]["Length"]

            dist_list[dist_num0].Dist_nbrs.append(stateG.nodes[e[1]]["District Number"])
            dist_list[dist_num1].Dist_nbrs.append(stateG.nodes[e[0]]["District Number"])

    for i in range(distcount):
        dist_list[i].Dist_nbrs = list(set(dist_list[i].Dist_nbrs))  #Extracts unique values


def pop_deviation(dist_list):
    '''Returns a single positive integer that sums each district's deviation from the ideal population. 
    Lower numbers for 'deviation' are better. A value of zero would indicate that every district has an equal number of people'''
    distcount = District.num_dists
    absdev = [0 for i in range(distcount - 1)]  #The -1 skips the dummy district
    
    for i in range(distcount - 1):
        if dist_list[i].Population != None:
            absdev[i] = abs(dist_list[i].Population - District.ideal_pop)
    deviation = round(sum(absdev))
    return deviation


def comp_score(dist_list, inverse=True):
    '''Computes the average Polsby-Popper score for a list of districts'''

    if inverse == False:
        comp_list = [d.PPCompactScore for d in dist_list]
    else: 
        comp_list = [d.invPPCompactScore for d in dist_list]
    
    comp_list = remove_nones(comp_list)

    if len(comp_list) != District.num_dists:
        raise ValueError("comp_score did not return the proper number of districts")
    PP_Comp_Score = sum(comp_list) / len(comp_list)  #Averages the compactness scores
    return PP_Comp_Score


def eg_score(dist_list, AV=False):
    '''Computes the average efficiency gap score for the map'''
    eg_list = District.EG_list(dist_list, AV)  #Gets list of efficiency gaps 
    eg_list = remove_nones(eg_list)

    if len(eg_list) != District.num_dists:
        raise ValueError("eg_score did not return the proper number of districts")
    eg_score = abs(sum(eg_list) / len(eg_list))  #Averages the EG score, then takes absolute values
    return eg_score


def median_mean(dist_list):
    """Returns the blue vote median-mean score for the map. 
    Positive numbers are considered beneficial for the blue party.
    We return the absolute value of the median-mean score,
    and want values of zero."""
    bs_list = District.blue_share_list(dist_list)
    bs_median = statistics.median(bs_list)
    bs_mean = sum(bs_list) / len(bs_list)
    bmm_score = bs_median - bs_mean
    return abs(bmm_score)


def initialize_map(ip, timetxt, num):
    """Generates an initial map using Spatially Constrained Multivariate Clustering"""
    #Counts number of rows in in_table      
    row_count = int(arcpy.GetCount_management(ip.in_table).getOutput(0))  #getOutput(0) returns the value at the first index position of a tool
    
    #Creates name for the output map
    out_table = ip.in_table + "_SA" + "_{0}".format(ip.distcount) + "dists" + timetxt + "_{}".format(num)

    #Using Spatially Constrained Multivariate Clustering to create a random starting district
    if not arcpy.ListFields(ip.in_table, "Test_val"):  #if field does not exist
        arcpy.AddField_management(ip.in_table, "Test_val", "LONG", field_alias="Test_val")
        print("Adding 'Test_val' field to in_table")
    with arcpy.da.UpdateCursor(ip.in_table, "Test_val") as cursor:
        for row in cursor:
            row[0] = random.randint(1,100000)
            cursor.updateRow(row)
        del cursor, row
    print("Running Spatially Constrained Multivariate Clustering to create the initial map...")
    
    mapflag = False
    failcount = 1
    while mapflag == False:  #We try SCMC to create an initial map. We have 20 attempts before the code gives up
        try:
            arcpy.stats.SpatiallyConstrainedMultivariateClustering(ip.in_table, out_table, "Test_val", size_constraints="NUM_FEATURES", min_constraint=0.65*row_count/ip.distcount, number_of_clusters=ip.distcount, spatial_constraints="CONTIGUITY_EDGES_ONLY")
            mapflag = True
            new_row_count = int(arcpy.GetCount_management(out_table).getOutput(0))  #Returns the number of rows in out_table
            if new_row_count != row_count:
                mapflag = False
                print("SCMC did not keep all GUs from the original map.")
                failcount = SCMC_restart(failcount, ip)
        except arcpy.ExecuteError:  #Occurs if SCMC cannot create a map with the given constraints
            mapflag = False
            failcount = SCMC_restart(failcount, ip)
            
    print("Spatially Constrained Multivariate Clustering succeeded.")
    
    #Adds populations as a column in out_table
    arcpy.JoinField_management(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_pop_field)
    
    #Adds vote totals as a column in out_table
    arcpy.JoinField_management(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_voteblue_field)
    arcpy.JoinField_management(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_votered_field)
    
    #Adds county numbers to out_table
    arcpy.JoinField_management(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_county_field)

    return out_table


def SCMC_restart(failcount, ip):
    """Protocol for restarting SCMC if necessary"""
    print("Attempt number {0} at using Spatially Constrained Multivariate Clustering (SCMC) failed. Trying again.".format(failcount))
    failcount = failcount + 1
    if failcount >= 20:
        raise RuntimeError("{0} attempts failed to produce a starting map for SCMC.".format(failcount))
    with arcpy.da.UpdateCursor(ip.in_table, 'Test_val') as cursor:  #Resets the random values
        for row in cursor:
            row[0] = random.randint(1, 100000)
            cursor.updateRow(row)
        del cursor, row
    return failcount


def main(*args):
    """main code"""
    CURRENTDIR = os.getcwd()
    PATH = CURRENTDIR + "\\SC_Redistricting_Updated.gdb"
    print("Current PATH is {}".format(PATH))
    arcpy.env.workspace = PATH
    arcpy.env.overwriteOutput = True
    in_table = PATH + "\\SC_Precincts_2021_v7"
    ip = input(7, in_table, args[0], "OBJECTID", "POPULATION", "PresBlue", "PresRed", "COUNTY")
    del in_table
    now = datetime.datetime.now()
    timetxt = now.strftime("_%m%d%y_%H%M")
    #Creates vectors of zeros that will hold values for population deviation, average compactness, etc.
    obj_vals = objective_vals(ip)
    ov = obj_vals  #An alias

    for j in range(ip.maps_created):
        #Creates an initial map using Spatially Constrained Multivariate Clustering
        out_table = {}  #Creates a dictionary that will hold all information about the out_table
        out_table["name"] = initialize_map(ip, timetxt, j)

        #Adds Area and Perimeter values to the out_table
        arcpy.CalculateGeometryAttributes_management(out_table["name"], [["Area_sq_km", "AREA_GEODESIC"], ["Perimeter_km", "PERIMETER_LENGTH_GEODESIC"]], "KILOMETERS", "SQUARE_KILOMETERS")

        #Assigns DistField as "Dist_Assign" and creates the field if it's not already there
        if not arcpy.ListFields(out_table["name"], "Dist_Assign"):
            arcpy.AddField_management(out_table["name"], "Dist_Assign", "SHORT", field_alias="DIST_ASSIGNMENT")
        out_table["dist_field"] = "Dist_Assign"

        #Adds a field named County_Num to out_table
        arcpy.AddField_management(out_table["name"], "County_Num", "SHORT", field_alias="County_Num")
        out_table["county_field"] = "County_Num"
        
        #Populates county_dict with 0-x, based on the sorted county numbers
        county_dict = make_county_dict(ip, out_table)
        
        #Initializes a list of lists that will categorize each geographic unit (GU) into its district
        #GU_list = [[ ] for d in range(ip.distcount)] 
        
        #Copies all CLUSTER_ID's into Dist_Assign and adds updated county numbers to out_table
        with arcpy.da.UpdateCursor(out_table["name"], [out_table["dist_field"], "CLUSTER_ID", "SOURCE_ID", "County", out_table["county_field"]]) as cursor:
            for row in cursor:
                row[0] = row[1]  #Dist_Assign = CLUSTER_ID
                row[4] = county_dict[int(row[3])]  #County_Num = sorted county value (if there are n counties, then this value will be between 0 and n-1)
                #GU_list[row[0] - 1].append(row[2])
                cursor.updateRow(row)
            del cursor, row
        
        #Creates dummy GU that surrounds the state
        create_buffer_dist(out_table)

        #Runs CreateNeighborList and returns the name of the neighbor_list
        neighbor_list = CreateNeighborList(out_table)
        
        #Creates an instance of District for each District and the dummy district (the GU surrounding the state)
        dist_list = [None] * (ip.distcount + 1)
        for i in range(ip.distcount):
            dist_list[i] = District(i)  #Initializes District variables for each district

        #Adds src_dist and nbr_dist to neighbor_list
        update_nbr_list(neighbor_list)

        stateG = build_adj_graph(out_table, neighbor_list, ip)

        #Finds district populations and adds them to the dist_list instances
        #find_dist_pops(ip, out_table, dist_list)

        populate_dist_list(stateG, dist_list)

        #Finds District Neighbor Pairs (dict) and returns the District Neighbor List (string). 
        #find_dist_nbrs(out_table, dist_list)

        #Finds compactness information 
        #[old_var, MapStats] = GraphMeasures.main(out_table["name"], out_table["dist_field"], ip.in_voteblue_field, ip.in_votered_field)  #Populates DistrictStats and MapStats using GraphMeasures
        # comp_list = [o.PPCompactScore for o in DistrictStats]  #comp is a list of compactness scores
        # for i in range(len(comp_list)): comp_list[i] = (1 / comp_list[i]) - 1  #Inverts the PP compactness score and subtracts 1 to make ideal value = 0
        #mm_value = MapStats.MedianMean  #mm_value is the Median Mean Score

        #Populates County-District-Intersection (CDI) values
        cdi_data = CDI(stateG)
        
        #print("The fairness scores for this map are: Median_Mean = {0}", fair)
        print("CDI_Count = {}".format(cdi_data.cdi_count))
        print("Total number of precincts (calculated by np.sum(cdi_data.cdi_mat)) = {0}".format(np.sum(cdi_data.cdi_mat)))



        #Populates the zeroth entry for all vectors
        ov.fill_obj_vals(pop_deviation(dist_list), comp_score(dist_list), eg_score(dist_list), cdi_data, median_mean(dist_list), "initialization", j, ip)
        del dist_list, cdi_data, stateG, out_table

    #Calculating standard deviation
    # pop_st_dev = np.std(ov.dev_vals)
    # comp_st_dev = np.std(ov.avg_comp_vals)
    # fair_st_dev = np.std(ov.fairscore_vals)
    # cdi_st_dev = np.std(ov.CDI_Count_vals)
    # egu_st_dev = np.std(ov.excess_GU_vals)

    # print("pop_st_dev = {}, comp_st_dev = {}, fair_st_dev = {}, cdi_st_dev = {}, egu_st_dev = {}".format(pop_st_dev, comp_st_dev, fair_st_dev, cdi_st_dev, egu_st_dev))
    print("\n")
    return ov



if __name__ == "__main__":
    main()