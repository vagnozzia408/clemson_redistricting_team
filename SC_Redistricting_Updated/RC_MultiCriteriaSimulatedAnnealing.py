# -*- coding: utf-8 -*-
"""
Created on Sun Jan 23 18:55:59 2022

@author: Blake Splitter with assistance from Amy Burton and Dr. Matthew Saltzman
"""

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



class input_vals:

    def __init__(self, in_t, in_p_f, in_n_f, in_c_f, in_vb_f, in_vr_f, dc,
                   nr, t, fin_t, tol, fin_tol, mfr, mff, pp, nf, obj_s, nipt, nm, mtu):
        self.in_table = in_t
        self.in_pop_field = in_p_f
        self.in_name_field = in_n_f
        self.in_county_field = in_c_f
        self.in_voteblue_field = in_vb_f
        self.in_votered_field = in_vr_f
        self.distcount = dc
        self.num_recoms = nr
        self.temp = t
        self.final_temp = fin_t
        self.tol = tol
        self.final_tol = fin_tol
        self.max_failed_recoms = mfr
        self.max_failed_flips = mff
        self.pop_perc = pp
        self.num_flips = nf
        self.objective_scales = obj_s
        self.num_its_per_temp = nipt
        self.num_maps = nm
        self.metrics_to_use = mtu

    def default_user_input(self):
        self.in_table = PATH + "\\SC_Precincts_2021_v7"
        self.in_pop_field = "POPULATION"
        self.in_name_field = "OBJECTID"
        self.in_county_field = "COUNTY"
        self.in_voteblue_field = "PresBlue"
        self.in_votered_field = "PresRed"
        self.distcount = 7
        self.num_recoms = 50
        self.temp = 20
        self.final_temp = 0.01
        self.tol = 30
        self.final_tol = 1
        self.max_failed_recoms = 15
        self.max_failed_flips = 5
        self.pop_perc = 15
        self.num_flips = 20
        self.objective_scales = [305242, 1.66856, 0.066641, 2.93654, 62.7187, 0.0127]  #These are the scaling factors for pop_dev, compactness, efficiency gap, EGU, CDI, and MM respectively
        self.num_its_per_temp = 10
        self.num_maps = 5
        self.metrics_to_use = [1, 1, 0, 1, 1, 1]  #Puts 1s in the spots for metrics we do want to use. [0]: Pop_dev, [1]: comp, [2]: eg, [3]: CDI, [4]: eGU, [5]: MM

    @property
    def coolingrate(self):
        """Calculates the necessary cooling rate to get from initial temperature to 
        final temperature in the requested number of recom steps"""
        return (self.final_temp / self.temp) ** (1 / self.num_recoms)

    @property
    def total_obj_vals_entries(self):
        """Returns the number of objective value entries needed"""
        return (self.num_its_per_temp*(self.num_recoms*(self.num_flips + 1)) + 1)


    @property
    def tol_coolingrate(self):
        """Calculates the cooling rate to get from starting tol to final tol"""
        return (self.final_tol / self.tol) ** (1 / self.num_recoms)

    @property
    def total_iterations(self):
        """Calculates the total number of loops in the SA algorithm we will do"""
        return self.num_recoms * self.num_its_per_temp


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

    def fill_obj_vals(self, dist_list, cdi_data, change, it, ip):
        self.dev_vals[it] = pop_deviation(dist_list)
        self.avg_comp_vals[it] = comp_score(dist_list)
        self.eg_score_vals[it] = eg_score(dist_list)
        self.CDI_Count_vals[it] = cdi_data.cdi_count
        self.excess_GU_vals[it] = cdi_data.excess_GU
        self.mm_vals[it] = median_mean(dist_list)
        self.change_type_vals[it] = change

        #ov.fill_obj_vals(pop_deviation(dist_list), comp_score(dist_list), eg_score(dist_list), cdi_data, median_mean(dist_list), "initialization", 0, ip)

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
            if self.Perimeter < 0:
                raise ValueError("Perimeter must be nonnegative.")
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


    def check_value_integrity(self):
        """Checks that all attributes make sense for the given district."""
        if self.Area < 0 or self.Population < 0 or self.Perimeter < 0 or self.VoteCountRed < 0 or self.VoteCountBlue < 0:
            raise ValueError("A metric in this district is negative.")


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
                units_in_CDI[stateG.nodes[n]["District Number"]][stateG.nodes[n]["County Number"] - 1] += 1

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
        if leaving_dist == 0 or entering_dist == 0:
            raise ValueError("Neither leaving_dist nor entering_dist should be 0.")
        self.cdi_mat[leaving_dist][stateG.nodes[GU]["County Number"] - 1] -= 1
        if self.cdi_mat[leaving_dist][stateG.nodes[GU]["County Number"] - 1] < 0:
            raise ValueError("Entries in the CDI matrix cannot be negative.")
        self.cdi_mat[entering_dist][stateG.nodes[GU]["County Number"] - 1] += 1

    """def upd_cdi_mat_recom(self, stateG, dist1, dist2):
        '''Updates the cdi matrix after a recombination'''
        self.cdi_mat[dist1] = np.zeros([1, self.num_counties], dtype=int)
        self.cdi_mat[dist2] = np.zeros([1, self.num_counties], dtype=int)"""



class counters:
    '''A class that will contain the counters used in the simulated annealing step'''
    def __init__(self):
        self.flipcount = 0  #The number of flips done in total in the code
        self.recomcount = 0  #The number of recombination steps done in total in the code
        self.failed_recom_counter = 0  #The number of consecutive failed recombination steps in the current iteration
        self.failed_flip_counter = 0  #The number of consecutive failed flip steps in the current flip attempt
        self.alphacount = 0  #The number of alpha values utilized previously
        self.its_at_temp = 0  #The number of iterations that have occurred at this temperature

    @property
    def currentit(self):
        '''Returns the sum of the flip count and the recom count'''
        return self.flipcount + self.recomcount  #This returns the index that will be populated in obj_vals

    def __repr__(self):
        return "flipcount = {0}. recomcount = {1}. failed_recom_counter = {2}. currentit = {3}".format(self.flipcount, self.recomcount, self.failed_recom_counter, self.currentit)


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


    def compare_objs(self, pareto_set, ip):
        """Compares the current map with all maps in the pareto set to determine if 
        1. The current map dominates at least one map in the pareto set
        2. The current map is dominated by at least one map in the pareto set
        3. The current map neither dominates nor is dominated by any map in the pareto set
        """
        nonequal_flag = False
        random.shuffle(pareto_set)
        for Map in pareto_set:
            objs_to_check = [(self.pop_dev, Map.pop_dev), 
                         (self.compactness, Map.compactness),
                         (self.eg, Map.eg), 
                         (self.cdi_num, Map.cdi_num), 
                         (self.excess_GU_num, Map.excess_GU_num), 
                         (self.mm, Map.mm)]
            for i in range(len(ip.metrics_to_use)):
                if ip.metrics_to_use[i] == 0:
                    objs_to_check[i] = None
            objs_to_check = remove_nones(objs_to_check)
            diff = []
            for entry in objs_to_check:
                diff.append(int(np.sign(entry[1] - entry[0])))  #old-new sign

            if list(set(diff)) == [0]:
                #This is the case where all metrics are equal. May occur if we compare self to self
                continue
            elif list(set(diff)) == [-1]:
                #This is the case where self is dominated
                return -1, Map
            elif list(set(diff)) == [1]:
                #This is the case where self dominates
                return 1, Map
            else:
                #This is the case where self neither dominates nor is dominated. 
                #We need to check all maps, so we pass here
                nonequal_flag = True  #signifies that at least one different map is in the Pareto set

        if nonequal_flag == False:
            return -2, -2  #Returns -2, -2 if the maps in the Pareto set all are exactly the same as self (this shouldn't happen)
        else:
            return 0, 0  #Returns 0, 0 if self is not dominated by any map and self does not dominate any map


def arcprint(message, *variables):
    '''
    Prints a message using arcpy.AddMessage() unless it can't; then it uses
    print.
    '''
    if RUNSPOT == "ArcGIS":
        arcpy.AddMessage(message.format(*variables))
    elif RUNSPOT == "console":
        newmessage = message
        variables = list(variables)
        j = 0
        while j < len(variables):  #This while loop puts the variable(s) in the correct spot(s) in the string
            if isinstance(variables[j], float):
                variables[j] = round(variables[j], 3)
            newmessage = newmessage.replace("{"+str(j)+"}",str(variables[j]))  #Replaces {i} with the ith variable
            j=j+1
        print(newmessage)
    else:
        raise RuntimeError("No value for RUNSPOT has been assigned")


def remove_nones(val_list):
    """Removes all 'None' entries from a list"""
    while True:
        try:
            val_list.remove(None)  #Removes None values from list
        except ValueError:
            break 
    return val_list


def build_alpha(metric_count, num_alphas):
    '''Builds the normalized weight vectors for use in simulated annealing'''
    alpha = np.zeros([num_alphas, metric_count], dtype=float)
    for i in range(num_alphas):
        for j in range(metric_count):
            alpha[i][j] = random.randint(1, 10000)
        alpha[i] = norm(alpha[i])
    return alpha


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


def initialize_map(ip, timetxt):
    """Generates an random initial map using Spatially Constrained Multivariate Clustering"""
    #Counts number of rows in in_table      
    row_count = int(arcpy.GetCount_management(ip.in_table).getOutput(0))  #getOutput(0) returns the value at the first index position of a tool
    
    #Creates name for the output map
    out_table = ip.in_table + "_SA" + "_{0}".format(ip.distcount) + "dists" + timetxt

    #Using Spatially Constrained Multivariate Clustering to create a random starting district
    if not arcpy.ListFields(ip.in_table, "Test_val"):  #if field does not exist
        arcpy.AddField_management(ip.in_table, "Test_val","LONG",field_alias="Test_val")
        arcprint("Adding 'Test_val' field to in_table")
    with arcpy.da.UpdateCursor(ip.in_table, 'Test_val') as cursor:
        for row in cursor:
            row[0] = random.randint(1,100000)
            cursor.updateRow(row)
        del cursor, row
    arcprint("Running Spatially Constrained Multivariate Clustering to create the initial map...")
    
    mapflag = False
    failcount = 1
    while mapflag == False:  #We try SCMC to create an initial map. We have 20 attempts before the code gives up
        try:
            arcpy.stats.SpatiallyConstrainedMultivariateClustering(ip.in_table, out_table, "Test_val", size_constraints="NUM_FEATURES", min_constraint=0.65*row_count/ip.distcount, number_of_clusters=ip.distcount, spatial_constraints="CONTIGUITY_EDGES_ONLY")
            mapflag = True
            new_row_count = int(arcpy.GetCount_management(out_table).getOutput(0))  #Returns the number of rows in out_table
            if new_row_count != row_count:
                mapflag = False
                arcprint("SCMC did not keep all GUs from the original map.")
                failcount = SCMC_restart(failcount, ip)
        except arcpy.ExecuteError:  #Occurs if SCMC cannot create a map with the given constraints
            mapflag = False
            failcount = SCMC_restart(failcount, ip)
            
    arcprint("Spatially Constrained Multivariate Clustering succeeded.")
    
    while True:
        #Adds populations as a column in out_table
        arcpy.JoinField_management(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_pop_field)
        
        #Adds vote totals as a column in out_table
        arcpy.JoinField_management(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_voteblue_field)
        arcpy.JoinField_management(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_votered_field)
        
        #Adds county numbers to out_table
        arcpy.JoinField_management(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_county_field)

        null_count = [0, 0, 0, 0]
        with arcpy.da.SearchCursor(out_table, [ip.in_pop_field, ip.in_voteblue_field, ip.in_votered_field, ip.in_county_field]) as cursor:
            for row in cursor:
                if row[0] == None: null_count[0] += 1
                if row[1] == None: null_count[1] += 1
                if row[2] == None: null_count[2] += 1
                if row[3] == None: null_count[3] += 1
            del cursor, row
        
        if null_count[0] > 1: 
            arcpy.DeleteField_management(out_table, ip.in_pop_field)
            arcpy.JoinField_management(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_pop_field)
        if null_count[1] > 1: 
            arcpy.DeleteField_management(out_table, ip.in_voteblue_field)
            arcpy.JoinField_management(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_voteblue_field)
        if null_count[2] > 1: 
            arcpy.DeleteField_management(out_table, ip.in_votered_field)
            arcpy.JoinField_management(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_votered_field)
        if null_count[3] > 1: 
            arcpy.DeleteField_management(out_table, ip.in_voteblue_field)
            arcpy.JoinField_management(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_county_field)
        if sum(null_count) == 0: break
        else: print("Null values were created in initialize map. Retrying JoinField_management.")

    return out_table


def SCMC_restart(failcount, ip):
    """Protocol for restarting SCMC if necessary"""
    arcprint("Attempt number {0} at using Spatially Constrained Multivariate Clustering (SCMC) failed. Trying again.", failcount)
    failcount = failcount + 1
    if failcount >= 20:
        raise RuntimeError("{0} attempts failed to produce a starting map for SCMC.".format(failcount))
    with arcpy.da.UpdateCursor(ip.in_table, 'Test_val') as cursor:  #Resets the random values
        for row in cursor:
            row[0] = random.randint(1, 100000)
            cursor.updateRow(row)
        del cursor, row
    return failcount


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

    arcprint("Deleting all rows from neighbor list with single-point adjacencies...")
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
            if row[0] == None:
                row[2] = 0
                row[0] = 0
            else:
                row[2] = row[0]  #src_dist = src_CLUSTER_ID

            if row[1] == None:
                row[3] = 0
                row[1] = 0
            else:
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

    arcprint("Creating the adjacency graph for all Geographical Units...")
    arcprint("Adding nodes to stateG...")
    with arcpy.da.SearchCursor(out_table["name"], [sf_name_field, sf_pop_field, out_table["county_field"], out_table["dist_field"], "Area_sq_km", ip.in_voteblue_field, ip.in_votered_field]) as cursor:
        for row in cursor:
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

    arcprint("Adding edges to stateG...")
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

    arcprint("Adding Population attribute")
    nx.set_node_attributes(stateG, popnum, "Population")
    arcprint("Adding District Number attribute")
    nx.set_node_attributes(stateG, distnum, "District Number")
    arcprint("Adding Original District Number attribute")
    nx.set_node_attributes(stateG, origdist, "Original District Number")
    arcprint("Adding County Number attribute")
    nx.set_node_attributes(stateG, countynum, "County Number")
    arcprint("Adding Area attribute")
    nx.set_node_attributes(stateG, area, "Area")
    arcprint("Adding Blue Vote attribute")
    nx.set_node_attributes(stateG, blue_votes, "Blue Votes")
    arcprint("Adding Red Vote attribute")
    nx.set_node_attributes(stateG, red_votes, "Red Votes")
    arcprint("Adding Length attribute for edges")
    nx.set_edge_attributes(stateG, length, "Length")
    arcprint("Adding Boundary status attribute for edges")
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

    arcprint("The starting population of each district is {0}. Thus, the ideal population for a district is {1}.", District.pop_list(dist_list), ideal_pop)

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


def flip(map_for_flip, temp, ip, GU=None, entering_dist=None):
    '''This is the flip algorithm. We move one GU across district lines. If GU and entering_dist are provided, then we consider that possible flip'''
    stateG = map_for_flip.graph
    dist_list = map_for_flip.dist_list
    cdi_data = map_for_flip.cdi_data
    #Records starting values for these inputs
    s_stateG = deepcopy(stateG)
    s_dist_list = deepcopy(dist_list)
    s_cdi_data = deepcopy(cdi_data)
    orig_GU = GU
    orig_ed = entering_dist

    adj_flag = False
    edge_count = stateG.number_of_edges()

    

    while adj_flag == False:
        
        if orig_GU == None:
            #This portion of code finds a random boundary edge
            boundaryflag = False

            while boundaryflag == False:
                rand_edge = random.randint(0, edge_count - 1)  #Selects a random edge from stateG.edges
                pair = list(stateG.edges)[rand_edge]
                n1 = pair[0]
                n2 = pair[1]
                if stateG.nodes[n1]["District Number"] == 0 or stateG.nodes[n2]["District Number"] == 0:  #If the node selected is the dummy node (which represents the dummy district)
                    continue  #Resets the loop if either node represents the dummy node
                if stateG[n1][n2]["Boundary"] == 1:  #If the edge represents a district boundary
                    boundaryflag = True
                else: 
                    continue  #Resets the loop if the edge does not represent a district boundary

        if orig_ed == None: 
            #This portion of code determines which GU will move
            r = random.randint(0,1)
            GU = pair[r]  #This is the GU that will move districts
            other_GU = pair[r - 1]  #If r = 0, then r - 1 = -1, which is the index for the last entry of the vector
            leaving_dist = stateG.nodes[GU]["District Number"]
            entering_dist = stateG.nodes[other_GU]["District Number"]
        else: leaving_dist = stateG.nodes[GU]["District Number"]

        if stateG.nodes[GU]["District Number"] == 0:
            raise RuntimeError("GU should not be selected as the dummy district in the Flip algorithm")

        DistrictNodes = [n for n in stateG.nodes() if stateG.nodes[n]["District Number"] == leaving_dist]  #Finds all nodes in leaving_dist
        DistrictNodes.remove(GU)
        sg_for_leaving_dist = stateG.subgraph(DistrictNodes)  #Creates a subgraph containing all nodes from DistrictNodes
        if nx.is_connected(sg_for_leaving_dist):
            adj_flag = True  #True if the leaving_dist is still contiguous
        else: 
            adj_flag = False  #Keeps the adj_flag at False if the move would create a discontiguity
            if orig_GU != None:
                return False  #Indicates that the desired flip creates a discontiguity
    
    #If entering dist was provided, we verify that the change does not create a discontiguity
    if orig_ed != None:
        adj_flag2 = False
        GU_nbrs = [nbr for nbr in stateG.neighbors(GU)]
        for nbr in GU_nbrs:
            if stateG.nodes[nbr]["District Number"] == entering_dist:
                adj_flag2 = True
                break
        if adj_flag2 == False:
            arcprint("GU cannot enter district {} because GU is not next to district {}".format(entering_dist, entering_dist)) 
            return False  #Indicates that Flip was unsuccessful




        # DistrictNodes2 = [n for n in stateG.nodes() if stateG.nodes[n]["District Number"] == entering_dist]  #Finds all nodes in leaving_dist
        # DistrictNodes2.append(GU)
        # sg_for_leaving_dist2 = stateG.subgraph(DistrictNodes2)  #Creates a subgraph containing all nodes from DistrictNodes
        # if nx.is_connected(sg_for_leaving_dist2):
        #     adj_flag2 = True  #True if the leaving_dist is still contiguous
        # else: 
        #     adj_flag2 = False  #Keeps the adj_flag at False if the move would create a discontiguity
        # if adj_flag2 == False:
        #     raise RuntimeError("GU cannot enter district {} because GU is not next to district {}".format(entering_dist, entering_dist))

    stateG.nodes[GU]["District Number"] = entering_dist  #Changes the district number in stateG

    for nbr in list(stateG.neighbors(GU)):  #Cycles through neighboring nodes to adjust boundary status, perimeter, and district neighbors
        nbr_dist = stateG.nodes[nbr]["District Number"]
        if nbr_dist == entering_dist:
            stateG[GU][nbr]["Boundary"] = 0
            dist_list[entering_dist].Perimeter -= stateG[GU][nbr]["Length"]  #This is now 'interior' perimeter
            dist_list[leaving_dist].Perimeter -= stateG[GU][nbr]["Length"]  #Neither GU nor nbr is in leaving_dist

        elif nbr_dist == 0:  #If nbr is the dummy district
            stateG[GU][nbr]["Boundary"] = 2
            dist_list[entering_dist].Perimeter += stateG[GU][nbr]["Length"]
            dist_list[leaving_dist].Perimeter -= stateG[GU][nbr]["Length"]
            dist_list[entering_dist].Dist_nbrs.append(nbr_dist)  #Add neighboring district to neighbor list. We delete duplicates later

        elif nbr_dist == leaving_dist:  #If nbr is part of the leaving_dist
            stateG[GU][nbr]["Boundary"] = 1
            dist_list[entering_dist].Perimeter += stateG[GU][nbr]["Length"]
            dist_list[leaving_dist].Perimeter += stateG[GU][nbr]["Length"]
            dist_list[entering_dist].Dist_nbrs.append(nbr_dist)  #Add neighboring district to neighbor list. We delete duplicates later

        else:  #Neighboring district is not entering_dist, leaving_dist, or the dummy district
            stateG[GU][nbr]["Boundary"] = 1
            dist_list[entering_dist].Perimeter += stateG[GU][nbr]["Length"]
            dist_list[leaving_dist].Perimeter -= stateG[GU][nbr]["Length"]
            dist_list[entering_dist].Dist_nbrs.append(nbr_dist)  #Add neighboring district to neighbor list. We delete duplicates later

    dist_list[entering_dist].Population += stateG.nodes[GU]["Population"]  #Adds population to the dist_list population entry corresponding to entering_dist
    dist_list[leaving_dist].Population -= stateG.nodes[GU]["Population"]  #Subtracts population from the dist_list population entry corresponding to leaving_dist
    
    dist_list[entering_dist].Area += stateG.nodes[GU]["Area"]  #Adds area to the dist_list area entry corresponding to entering_dist
    dist_list[leaving_dist].Area -= stateG.nodes[GU]["Area"]  #Subtracts area from the dist_list area entry corresponding to leaving_dist

    dist_list[entering_dist].VoteCountRed += stateG.nodes[GU]["Red Votes"]  #Adds red votes to the dist_list red votes entry corresponding to entering_dist
    dist_list[leaving_dist].VoteCountRed -= stateG.nodes[GU]["Red Votes"]  #Subtracts red votes from the dist_list red votes entry corresponding to leaving_dist

    dist_list[entering_dist].VoteCountBlue += stateG.nodes[GU]["Blue Votes"]  #Adds blue votes to the dist_list blue votes entry corresponding to entering_dist
    dist_list[leaving_dist].VoteCountBlue -= stateG.nodes[GU]["Blue Votes"]  #Subtracts blue votes from the dist_list blue votes entry corresponding to leaving_dist

    dist_list[entering_dist].Dist_nbrs = list(set(dist_list[entering_dist].Dist_nbrs))  #Extracts unique values

    cdi_data.upd_cdi_mat_flip(stateG, GU, leaving_dist, entering_dist)  #Updates the CDI matrix

    map_u = Map_class(s_stateG, map_for_flip.alpha, s_dist_list, s_cdi_data)  #old
    map_v = Map_class(stateG, map_for_flip.alpha, dist_list, cdi_data)  #new, proposed

    if temp == None: return True
    do_flip = sa_prob_calc(map_v, map_u, temp, ip)
    if orig_GU == None and do_flip == True:  #Prints only if outside of hill_climbing
        arcprint("Completed Flip algorithm. Flipped GU {0} from district {1} to district {2}.", GU, leaving_dist, entering_dist)
    return do_flip  #Will return True if the flip should be done, False otherwise


def recom(map_v, tol, count, dist1=None, dist2=None):
    '''Does a Recombination step for the graph stateG'''
    #1. Determine if two districts are adjacent
    #2. Grab all GUs from those two districts and create a subgraph. 
    #3. Error check: Verify that the subgraph is connected
    #4. Wilson's Algorithm
    #5. Make sure that the resulting tree acquires all attributes from stateG
    #6. FindEdgeCut
    #7. Reassign the new subgraphs to their proper districts
    stateG = map_v.graph
    dist_list = map_v.dist_list
    distcount = len(set(dict(stateG.nodes("District Number")).values())) - 1  #Finds number of unique districts (-1 excludes dummy district)
    dist_adj_flag = False
    orig_dist1 = dist1
    orig_dist2 = dist2
    if orig_dist1 != None:
        if orig_dist1 > distcount:
            arcprint("dist1 was too large. We will randomly reselect this district.")
    if orig_dist2 != None:
        if orig_dist2 > distcount:
            arcprint("dist2 was too large. We will randomly reselect this district.")

    while dist_adj_flag == False:
        if orig_dist1 == None or orig_dist1 > distcount:
            dist1 = random.randint(1, distcount)  #Randomly selects dist1 if it wasn't provided as input or if it is out of range
        if orig_dist2 == None or orig_dist2 > distcount:
            dist2 = random.randint(1, distcount)  #Randomly selects dist2 if it wasn't provided as input or if it is out of range
        if dist2 not in dist_list[dist1].Dist_nbrs or dist1 not in dist_list[dist2].Dist_nbrs:
            continue  #Restarts the loop if this district neighbor pair can't be located in dist_list

        dist1_and_dist2_nodes = []
        for n in stateG.nodes(): 
            if stateG.nodes[n]["District Number"] == dist1 or stateG.nodes[n]["District Number"] == dist2:
                dist1_and_dist2_nodes.append(n)
        two_dist_graph = stateG.subgraph(dist1_and_dist2_nodes)  #Creates a subgraph of the two districts
        if nx.is_connected(two_dist_graph) == False:
            arcprint("District {0} and District {1} are not adjacent. Reselecting districts", dist1, dist2)
            try:
                dist_list[dist1].Dist_nbrs.remove(dist2)
            except ValueError:
                pass
            try:
                dist_list[dist2].Dist_nbrs.remove(dist1)
            except ValueError:
                pass
            dist_adj_flag = False  #Keeps the flag at False

        else:  #If the two districts are indeed adjacent
            dist_adj_flag = True
    
    tree = wilson(two_dist_graph, random)  #Creates a uniform random spanning tree for two_dist_graph using Wilson's algorithm
    subgraphs = find_edge_cut(tree, tol)  #Finds an edge to remove from the tree to create two districts

    #This next section of code decides which subgraph should become district 1 and which should become district 2
    if subgraphs:  #If subgraphs is not empty
        s0d1count = 0
        s0d2count = 0
        s1d1count = 0
        s1d2count = 0
        for i in subgraphs[0]: 
            if stateG.nodes[i]["District Number"] == dist1:
                s0d1count += 1
            elif stateG.nodes[i]["District Number"] == dist2:
                s0d2count += 1
        for i in subgraphs[1]:
            if stateG.nodes[i]["District Number"] == dist1:
                s1d1count += 1
            elif stateG.nodes[i]["District Number"] == dist2:
                s1d2count += 1
        
        #Assigns either dist1 or dist2 to the moved GUs
        if s0d1count + s1d2count >= s0d2count + s1d1count:
            for i in subgraphs[0]:
                stateG.nodes[i]["District Number"] = dist1
            for i in subgraphs[1]:
                stateG.nodes[i]["District Number"] = dist2
        
        else:
            for i in subgraphs[0]:
                stateG.nodes[i]["District Number"] = dist2
            for i in subgraphs[1]:
                stateG.nodes[i]["District Number"] = dist1
        
        #Resets dist_list entries
        dist_list[dist1].reset_vals()
        dist_list[dist2].reset_vals()

        #Cycles through nodes to update boundary list
        for GU in two_dist_graph.nodes:
            GU_dist = stateG.nodes[GU]["District Number"]
            for nbr in list(stateG.neighbors(GU)):  #Cycles through neighboring nodes to update boundary status, perimeter, and Dist_nbrs
                nbr_dist = stateG.nodes[nbr]["District Number"]

                if nbr_dist == GU_dist: 
                    stateG[GU][nbr]["Boundary"] = 0
                    dist_list[GU_dist].Perimeter += 0 

                elif nbr_dist == 0:  #If nbr is the dummy node
                    stateG[GU][nbr]["Boundary"] = 2
                    dist_list[GU_dist].Perimeter += stateG[GU][nbr]["Length"]
                    dist_list[GU_dist].Dist_nbrs.append(0)

                else:  #If the GU and nbr are in different districts
                    stateG[GU][nbr]["Boundary"] = 1
                    dist_list[GU_dist].Dist_nbrs.append(nbr_dist)
                    dist_list[GU_dist].Perimeter += stateG[GU][nbr]["Length"]

            #Updates the dist_list instance
            dist_list[GU_dist].Area += stateG.nodes[GU]["Area"]
            dist_list[GU_dist].Population += stateG.nodes[GU]["Population"]
            dist_list[GU_dist].VoteCountRed += stateG.nodes[GU]["Red Votes"]
            dist_list[GU_dist].VoteCountBlue += stateG.nodes[GU]["Blue Votes"]

            dist_list[GU_dist].check_value_integrity()  #Returns an error if anything is negative
        
        dist_list[dist1].Dist_nbrs = list(set(dist_list[dist1].Dist_nbrs))  #Isolates unique values
        dist_list[dist2].Dist_nbrs = list(set(dist_list[dist2].Dist_nbrs))  #Isolates unique values

        map_v.cdi_data = CDI(stateG)  #Reinitializes the CDI data after this recom step.

        arcprint("Recom number {0} succeeded. Reorganized districts {1} and {2}", count.recomcount, dist1, dist2)
        


        return True  #Indicates that the recom_success_flag is True
    else:  #If subgraphs were empty (i.e. we couldn't find an edge to cut that split population within tolerance)
        return False  #Indicates that the recom_success_flag is False


def wilson(graph, rng):
    '''Returns a uniform spanning tree on G'''
    walk = loopErasedWalk(graph, rng)
    currentNodes = [n for n in walk]

    uniformTree = nx.Graph()
    for i in range(len(walk) - 1):
        uniformTree.add_edge(walk[i], walk[i + 1])

    treeNodes = set(uniformTree.nodes)
    neededNodes = set(graph.nodes) - treeNodes

    while neededNodes:
        v = rng.choice(sorted(list(neededNodes))) # sort for code repeatability
        walk = loopErasedWalk(graph, rng, v1 = [v], v2 = currentNodes)
        currentNodes += walk
        for i in range(len(walk) - 1):
            uniformTree.add_edge(walk[i], walk[i + 1])
        treeNodes = set(uniformTree.nodes)
        neededNodes = set(graph.nodes) - treeNodes

    pass 
    nx.set_node_attributes(uniformTree, dict(graph.nodes("Population")), "Population")
    nx.set_node_attributes(uniformTree, dict(graph.nodes("District Number")), "District Number")
    nx.set_node_attributes(uniformTree, dict(graph.nodes("Original District Number")), "Original District Number")
    nx.set_node_attributes(uniformTree, dict(graph.nodes("County Number")), "County Number")
    nx.set_node_attributes(uniformTree, dict(graph.nodes("Area")), "Area")
    nx.set_node_attributes(uniformTree, dict(graph.nodes("Blue Votes")), "Blue Votes")
    nx.set_node_attributes(uniformTree, dict(graph.nodes("Red Votes")), "Red Votes")
    nx.set_edge_attributes(uniformTree, dict(graph.edges("Length")), "Length")
    nx.set_edge_attributes(uniformTree, dict(graph.edges("Boundary")), "Boundary")
    return uniformTree


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


def find_edge_cut(tree, tol):
    '''Input a tree graph and a percent tolerance. The function will remove a 
    random edge that splits the tree into two pieces such that each piece 
    has population within that percent tolerance. The variable 'tol' should be a positive real 
    number in (0,100].'''
    if tol > 100 or tol <= 0 or (isinstance(tol, float) == False and isinstance(tol, int) == False): 
        raise ValueError("tol must be a float or integer variable in the range (0,100].")
    if nx.is_tree(tree) == False:
        raise ValueError("The input graph must be a tree.")
    tree_edge_list = list(tree.edges)
    random.shuffle(tree_edge_list)  #Randomly shuffles the edges of T
    e = None
    num_edges = len(tree_edge_list)
    
    for i in range(num_edges):
        e = tree_edge_list[i]  #Edge to delete
        tree.remove_edge(*e)
        subgraphs = nx.connected_components(tree)
        subgraphs_lst = list(subgraphs)
        subgraphs_lst[0] = sorted(subgraphs_lst[0])
        subgraphs_lst[1] = sorted(subgraphs_lst[1])
        dist_pop1 = sum(value for key, value in nx.get_node_attributes(tree, "Population").items() if key in subgraphs_lst[0])  #Finds population sum for first district
        dist_pop2 = sum(value for key, value in nx.get_node_attributes(tree, "Population").items() if key in subgraphs_lst[1])  #Finds population sum for second district
        total_pop = dist_pop1 + dist_pop2
        avg_pop = total_pop / 2
        if abs(dist_pop1 - avg_pop) > 0.01 * tol * avg_pop or abs(dist_pop2 - avg_pop) > 0.01 * tol * avg_pop:  #If both proposed districts are outside the prescribed tolerance
            tree.add_edge(*e)  #Adds the edge back to the tree if it didn't meet the tolerance
        else:  #This is what we want: both proposed districts within the prescribed tolerance
            if i == 0:
                pass
                #arcprint("Population requirement was met. Removing edge {0}. Required {1} iteration.", e, i+1)
            else: 
                pass
                #arcprint("Population requirement was met. Removing edge {0}. Required {1} iterations.", e, i+1)
            return subgraphs_lst
        if i == num_edges - 1:
            #arcprint("No subgraphs with appropriate criteria requirements were found. Required {0} iterations.\n", i+1)
            return []  #Returns empty subgraphs list if no appropriate subgraphs were found.


def sa_prob_calc(map_v, map_u, temp, ip):
    """Uses simulated annealing architecture to determine whether we should discard map_v or make it our current solution. 
    Positive values for delta_f are preferred, since we are subtracting old solution minus new solution. """
    pop_dev_diff = map_u.pop_dev - map_v.pop_dev
    compactness_diff = map_u.compactness - map_v.compactness
    eg_diff = map_u.eg - map_v.eg
    cdi_diff = map_u.cdi_num - map_v.cdi_num
    eGU_diff = map_u.excess_GU_num - map_v.excess_GU_num
    mm_diff = map_u.mm - map_v.mm

    #These obj_diffs are weighted so that all objectives are of similar value
    obj_diffs = [None] * len(ip.metrics_to_use)
    obj_diffs[0] = pop_dev_diff / ip.objective_scales[0] if ip.metrics_to_use[0] == 1 else None
    obj_diffs[1] = compactness_diff / ip.objective_scales[1] if ip.metrics_to_use[1] == 1 else None
    obj_diffs[2] = eg_diff / ip.objective_scales[2] if ip.metrics_to_use[2] == 1 else None
    obj_diffs[3] = cdi_diff / ip.objective_scales[3] if ip.metrics_to_use[3] == 1 else None
    obj_diffs[4] = eGU_diff / ip.objective_scales[4] if ip.metrics_to_use[4] == 1 else None
    obj_diffs[5] = mm_diff / ip.objective_scales[5] if ip.metrics_to_use[5] == 1 else None

    obj_diffs = remove_nones(obj_diffs)

    delta_f = np.dot(map_u.alpha, obj_diffs)
    try:
        rho = math.exp(delta_f / temp) if delta_f < 0 else 1  #If delta_f < 0, we got worse. 
    except OverflowError:
        rho = 0
    if rho > 1 or rho < 0:
        raise ValueError("rho should be between 0 and 1. rho = {0}".format(rho))
    r = random.uniform(0,1)
    if r <= rho:

        return True  
    else:
        return False


def replace_map(pareto_set, map_p, map_v):
    """Replaces map_p in the Pareto set with map_v"""
    map_v.alpha = map_p.alpha
    pareto_set.remove(map_p)
    pareto_set.append(map_v)
    return pareto_set


def select_map_to_perturb(map_v):
    """The map that we want to perturb is the input. We return copies of stateG, 
    dist_list, and cdi_data so that we don't unintentionally change data for map_v."""
    map_u = deepcopy(map_v)
    stateG = deepcopy(map_u.graph)
    dist_list = deepcopy(map_u.dist_list)
    cdi_data = deepcopy(map_u.cdi_data)
    return stateG, dist_list, cdi_data, map_u.alpha


def add_alpha_row(alpha):
    """Adds a row to alpha"""
    metric_count = alpha.shape[1]  #Gets number of columns from alpha
    newrow = [0] * metric_count
    tot = 0
    for i in metric_count:
        newrow[i] = random.randint(1, 10000)
        tot += newrow[i]
    for i in metric_count:
        newrow[i] = newrow[i] / tot
    alpha = np.vstack([alpha, newrow])
    eps = 0.000001
    if sum(newrow) > 1 + eps or sum(newrow) < 1 - eps:
        raise ValueError("The elements of alpha must sum to 1. newrow = {0}".format(newrow))


def hill_climbing(pareto_set, ip):
    """We search for local optima for all maps in the Pareto set."""
    arcprint("Beginning hill climbing algorithm.")
    for i in range(len(pareto_set)):
        arcprint("Examining map {0} from pareto set", i)
        curr_graph = deepcopy(pareto_set[i].graph)
        dist_list = deepcopy(pareto_set[i].dist_list)
        cdi_data = deepcopy(pareto_set[i].cdi_data)
        
        all_edges_searched = False
        while all_edges_searched == False:
            map_for_flip = Map_class(curr_graph, pareto_set[i].alpha, dist_list, cdi_data)
            map_before_flip = deepcopy(map_for_flip)
            boundary_edges = []
            boundary_edges = find_boundary_edges(curr_graph)
            for e in boundary_edges:
                n0 = e[0]
                n1 = e[1]
                dist0 = curr_graph.nodes[n0]["District Number"]
                dist1 = curr_graph.nodes[n1]["District Number"]
                if dist0 == dist1:
                    arcprint("This is problematic. dist0 = dist1. This shouldn't happen.")
                if dist0 == 0 or dist1 == 0: 
                    break  #Returns to while loop if either district is the dummy district

                #Consider moving n0 into dist1
                flip_status = flip(map_for_flip, None, ip, n0, dist1)  #If flip_status is True, then the flip doesn't create discontiguities
                if flip_status == True:
                    if boundary_check(map_for_flip.graph) == False: print("Boundaries are incorrect")

                    code, map_p = map_for_flip.compare_objs([pareto_set[i]], ip)  #We are comparing objectives ONLY with the map for pareto_set[i]
                    if code == 1:  #Indicating that the flip improved the map...
                        pareto_set = replace_map(pareto_set, map_p, map_for_flip)  #Replaces map_p with map_for_flip in PS
                        arcprint("Flipping GU {} from district {} to district {} improved all metrics. Making this flip.".format(n0, dist0, dist1))
                        all_edges_searched = False  #Keeps this flag at False
                        break  #Resets to the while loop
                    else: 
                        map_for_flip = deepcopy(map_before_flip)  #Undoes the flip
                        #flip_status = flip(map_for_flip, None, ip, n0, dist0)  #Undoes the flip
                
                #Consider moving n1 into dist0
                flip_status = flip(map_for_flip, None, ip, n1, dist0)  #If flip_status is True, then the flip doesn't create discontiguities
                if flip_status == True:
                    if boundary_check(map_for_flip.graph) == False: print("Boundaries are incorrect") 
                    code, map_p = map_for_flip.compare_objs([pareto_set[i]], ip)  #We are comparing objectives ONLY with the map for pareto_set[i]
                    if code == 1:  #Indicating that the flip improved the map...
                        pareto_set = replace_map(pareto_set, map_p, map_for_flip)  #Replaces map_p with map_for_flip in PS
                        arcprint("Flipping GU {} from district {} to district {} improved all metrics. Making this flip.".format(n1, dist1, dist0))
                        all_edges_searched = False  #Keeps this flag at False
                        break  #Resets to the while loop
                    else:
                        map_for_flip = deepcopy(map_before_flip)  #Undoes the flip
                        #flip_status = flip(map_for_flip, None, ip, n1, dist1)  #Undoes the flip
            if e == boundary_edges[-1]:
                all_edges_searched = True
    return pareto_set


def find_boundary_edges(graph):
    """Finds all edges for a graph that are on district boundaries"""
    boundary_list = [(u,v) for u,v,e in graph.edges(data=True) if e["Boundary"] == 1]  #Selects all edges on district boundaries
    return boundary_list


def boundary_check(graph):
    """Determines if the edges of the graph correctly identify district boundaries"""
    return True
    for e in graph.edges:
        n0 = e[0]
        n1 = e[1]
        dist0 = graph.nodes[n0]["District Number"]
        dist1 = graph.nodes[n1]["District Number"]
        boundary_status = graph[n0][n1]["Boundary"]
        if dist0 == dist1 and (boundary_status == 1 or boundary_status == 2):
            arcprint("This edge {0} is a problem.", e)
            return False
        elif dist0 != dist1 and boundary_status == 0:
            arcprint("This edge {0} is a problem.", e)
            return False
        elif (dist0 == 0 or dist1 == 0) and (boundary_status == 0 or boundary_status == 1):
            arcprint("This edge {0} is a problem.", e)
            return False
    return True



def main(*args):
    """Runs the primary instance of the algorithm."""
    global RUNSPOT  #Allows RUNSPOT to be changed inside a function
    if sys.executable == r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe":  #Change this line if ArcGIS is located elsewhere
        RUNSPOT = "ArcGIS"
    else:
        RUNSPOT = "console"

    # Set environment settings
    global CURRENTDIR
    global PATH

    CURRENTDIR = os.getcwd()
    PATH = CURRENTDIR + "\\SC_Redistricting_Updated.gdb"
    arcprint("Current PATH is {0}", PATH)
    arcpy.env.workspace = PATH
    arcpy.env.overwriteOutput = True

    #Get user input
    sig = signature(input_vals.__init__)
    if len(sys.argv) == len(sig.parameters):
        arcprint("Using sys.argv")
        ip = input_vals(sys.argv)  #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
        ###Probably want to input a function that verifies all user input is acceptable
    elif len(args) == len(sig.parameters):
        arcprint("Using args")
        ip = input_vals(args)  #Second, tries to take input from explicit input into main()
        ###Probably want to input a function that verifies all user input is acceptable
    else:
        arcprint("Using default variable choices")
        #Inserting dummy values to be overwritten in next line
        ip = input_vals(None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
        ip.default_user_input()  #Finally, manually assigns input values if they aren't provided

    #Marking the start time of the run.
    now = datetime.datetime.now()
    arcprint("Starting date and time : {0}", now.strftime("%m-%d-%y %H:%M:%S"))
    timetxt = now.strftime("_%m%d%y_%H%M")

    #This builds alpha, which is the normalized unit vector that details how much we care about any given metric.
    metric_count = sum(ip.metrics_to_use)
    alpha = build_alpha(metric_count, ip.num_maps)

    tol = ip.tol  #tol will be modified later
    temp = ip.temp  #temp will be modified later

    #Creates an initial map using Spatially Constrained Multivariate Clustering
    out_table = {}  #Creates a dictionary that will hold all information about the out_table
    out_table["name"] = initialize_map(ip, timetxt)

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

    populate_dist_list(stateG, dist_list)

    #Populates County-District-Intersection (CDI) values
    cdi_data = CDI(stateG)
    arcprint("CDI_Count = {0}", cdi_data.cdi_count)
    arcprint("Total number of precincts (calculated by np.sum(cdi_data.cdi_mat)) = {0}", np.sum(cdi_data.cdi_mat))

    #Creates vectors of zeros that will hold values for population deviation, average compactness, etc.
    obj_vals = objective_vals(ip)
    ov = obj_vals  #An alias

    #Populates the zeroth entry for all vectors
    ov.fill_obj_vals(dist_list, cdi_data, "initialization", 0, ip)

    #Initializing the main line of the Simulated Annealing Algorithm
    count = counters()  #Keeps track of the various counters needed
    pareto_set = []  #The list that will contain all high-quality maps in the Pareto Set

    #Populates zeroth entry for the pareto set
    map0 = Map_class(stateG, alpha[0], dist_list, cdi_data)
    count.alphacount = 1  #We used the first alpha value in the previous line
    pareto_set.append(map0)
    stateG = deepcopy(stateG)  #Creates a new instance of stateG so that future changes won't affect map0
    dist_list = deepcopy(dist_list)
    cdi_data = deepcopy(cdi_data)
    #map_u = deepcopy(map0)

    #Starting the main line of the Simulated Annealing Algorithm
    while count.recomcount < ip.total_iterations:
        if temp == ip.temp: alpha_val = map0.alpha
        map_v = Map_class(stateG, alpha_val, dist_list, cdi_data)
        for i in range(ip.num_flips):
            count.failed_flip_counter = 0  #Resets the failed_flip_counter
            flip_success_flag = False
            while flip_success_flag == False and count.failed_flip_counter < ip.max_failed_flips:
                flip_success_flag = flip(map_v, temp, ip)  #Does the Flip algorithm and returns "True" if flip succeeded
                if flip_success_flag == False: count.failed_flip_counter += 1
            count.flipcount += 1
            if flip_success_flag == True: 
                ov.fill_obj_vals(dist_list, cdi_data, "flip", count.currentit, ip)
            else: 
                arcprint("Flip algorithm failed after {0} attempts. Skipping this flip.", count.failed_flip_counter)
                ov.fill_obj_vals(dist_list, cdi_data, "failed_flip", count.currentit, ip)
            if boundary_check(map_v.graph) == False: print("Boundaries are incorrect") 
                
            
            

        count.failed_recom_counter = 0  #Resets the failed_recom_counter
        recom_success_flag = False
        while recom_success_flag == False:
            recom_success_flag = recom(map_v, tol, count)  #Does recombination algorithm and returns "True" if recom succeeded
            if recom_success_flag == False: count.failed_recom_counter += 1
            if count.failed_recom_counter >= ip.max_failed_recoms:
                arcprint("We failed in {0} consecutive recom attempts. Skipping this recom step.", count.failed_recom_counter)
                break
        count.recomcount += 1
        if boundary_check(map_v.graph) == False: print("Boundaries are incorrect") 
        if recom_success_flag == True:
            ov.fill_obj_vals(dist_list, cdi_data, "recom", count.currentit, ip)
        else: 
            ov.fill_obj_vals(dist_list, cdi_data, "failed_recom", count.currentit, ip)
        
        code, map_p = map_v.compare_objs(pareto_set, ip)

        if code == 1:  #If perturbed map is dominant
            pareto_set = replace_map(pareto_set, map_p, map_v)  #Replaces map_p with map_v in PS
            stateG, dist_list, cdi_data, alpha_val = select_map_to_perturb(map_v)
            arcprint("map_v is dominant over a map in the Pareto set. Adding map_v to the Pareto set.")
            
        elif code == 0 and len(pareto_set) < ip.num_maps:  #If the perturbed map is neither dominated nor dominant over any PS maps and there are fewer than 10 maps in the PS
            try:
                map_v.alpha = alpha[count.alphacount]
            except IndexError:  #In case we didn't build enough alpha values in the beginning
                add_alpha_row(alpha)
                map_v.alpha = alpha[count.alphacount]
            count.alphacount += 1
            pareto_set.append(map_v)
            stateG, dist_list, cdi_data, alpha_val = select_map_to_perturb(map_v)
            arcprint("map_v is middling. Adding map_v to the Pareto set since there aren't yet {0} maps in the PS.", ip.num_maps)

        elif code == 0 and len(pareto_set) >= ip.num_maps:  #If the perturbed map is neither dominated nor dominant over any PS maps and there are at least 10 maps in the PS
            map_p = random.choice(pareto_set)  #A random map from the Pareto set
            add_to_PS = sa_prob_calc(map_v, map_p, temp, ip)
            if add_to_PS == True: 
                pareto_set = replace_map(pareto_set, map_p, map_v)
                arcprint("map_v is middling. By the SA probability, we add this to the PS.")
            else: 
                arcprint("map_v is middling. By the SA probability, we DO NOT add this to the PS.")

            accept_perturbation = sa_prob_calc(map_v, map_p, temp, ip)
            if accept_perturbation == True:
                stateG, dist_list, cdi_data, alpha_val = select_map_to_perturb(map_v)
                arcprint("We will continue to make perturbations to map_v.")
            else:
                stateG, dist_list, cdi_data, alpha_val = select_map_to_perturb(random.choice(pareto_set))
                arcprint("Discarding map_v and reselecting a map from the Pareto set.")

        elif code == -1:  #If the perturbed map is dominated by some map in the pareto set
            accept_perturbation = sa_prob_calc(map_v, map_p, temp, ip)
            arcprint("map_v is dominated by a map in the Pareto set. We will not add it to the PS.")
            if accept_perturbation == True:
                stateG, dist_list, cdi_data, alpha_val = select_map_to_perturb(map_v)
                arcprint("We will continue to make perturbations to map_v.")
            else:
                stateG, dist_list, cdi_data, alpha_val = select_map_to_perturb(random.choice(pareto_set))
                arcprint("Discarding map_v and reselecting a map from the Pareto set.")

        elif code == -2:
            raise RuntimeError("All maps in the Pareto set match the perturbed map. This should not happen.")

        else:
            raise RuntimeError("Unexpected code returned. code = {}".format(code))

        print("\n")

        #Reduces temperature and tolerance if we've done the proper number of iterations at this temperature
        count.its_at_temp += 1
        if count.its_at_temp >= ip.num_its_per_temp:
            count.its_at_temp = 0
            temp = temp * ip.coolingrate
            tol = tol * ip.tol_coolingrate

    #Beginning search for local optima
    #pareto_set = hill_climbing(pareto_set, ip)

    print("Starting data:")
    starting_data = [[map0.pop_dev, map0.compactness, map0.eg, map0.cdi_num, map0.excess_GU_num, map0.mm]]
    df = pd.DataFrame(starting_data, columns = ["Population Deviation", "Compactness", "Efficiency Gap", "CDI", "excess GU", "Median Mean"])
    print(df)

    data_table = []
    for i in range(len(pareto_set)):
        data_table.append([pareto_set[i].pop_dev, pareto_set[i].compactness, pareto_set[i].eg, pareto_set[i].cdi_num, pareto_set[i].excess_GU_num, pareto_set[i].mm])
    df2 = pd.DataFrame(data_table, columns = ["Population Deviation", "Compactness", "Efficiency Gap", "CDI", "excess GU", "Median Mean"])
    print(df2)

    


    for i in range(len(pareto_set)):
        dist_field_name = "PS{}_district".format(i)
        if not arcpy.ListFields(out_table["name"], dist_field_name):  #if field does not exist
            arcpy.AddField_management(out_table["name"], dist_field_name, "SHORT", field_alias="Pareto Set {} District".format(i))
            with arcpy.da.UpdateCursor(out_table["name"], [dist_field_name, "OBJECTID"]) as cursor:
                for row in cursor:
                    n = int(row[1])
                    row[0] = pareto_set[i].graph.nodes[n]["District Number"]
                    cursor.updateRow(row)
                del cursor, row





        # table_name = out_table["name"] + "_PS_" + "{}".format(i)
        # arcpy.Copy_management(out_table["name"], table_name)  #Will create a unique map for each graph

        # #Adds Dist_Assign values back to GUs in map
        # with arcpy.da.UpdateCursor(table_name, [out_table["dist_field"], "OBJECTID"]) as cursor:
        #     for row in cursor:
        #         n = int(row[1])
        #         row[0] = pareto_set[i].graph.nodes[n]["District Number"]
        #         cursor.updateRow(row)
        #     del cursor, row

    ending_time = datetime.datetime.now()
    arcprint("Ending date and time : {0}", ending_time.strftime("%m-%d-%y %H:%M:%S"))
    elapsed_time = ending_time - now
    arcprint("Elapsed time = {0}", elapsed_time)
    arcprint("We finished!")
        







if __name__ == "__main__":
    main()
