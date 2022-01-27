# -*- coding: utf-8 -*-
"""
Created on Sun Jan 23 18:55:59 2022

@author: Blake Splitter
"""

import sys
import os
import arcpy
import datetime
import random
from inspect import signature


class input_vals:
    in_table = ""
    in_pop_field = ""
    in_name_field = ""
    in_county_field = ""
    in_voteblue_field = ""
    in_votered_field = ""
    distcount = 0
    max_iter = 0
    temp = float(0)
    final_t = 0
    coolingrate = float(0)
    tol = float(0)
    maxstopcounter = 0
    #alpha = [float(0)] * 5
    pop_perc = float(0)
    naming_convention = ""
    num_maps = 0

    def user_input(self, in_t, in_p_f, in_n_f, in_c_f, in_vb_f, in_vr_f, dc,
                   mi, t, fin_t, tol, msc, pp, nm):
        self.in_table = in_t
        self.in_pop_field = in_p_f
        self.in_name_field = in_n_f
        self.in_county_field = in_c_f
        self.in_voteblue_field = in_vb_f
        self.in_votered_field = in_vr_f
        self.in_distcount = dc
        self.max_iter = mi
        self.temp = t
        self.final_t = fin_t
        self.coolingrate = (fin_t/t)**(1/mi)
        self.tol = tol
        self.maxstopcounter = msc
        #self.alpha = al
        self.pop_perc = pp
        #self.naming_convention = nc
        self.num_maps = nm

    def default_user_input(self):
        self.in_table = PATH + "\\SC_Precincts_2021_v7"
        self.in_pop_field = "POPULATION"
        self.in_name_field = "OBJECTID"
        self.in_county_field = "COUNTY"
        self.in_voteblue_field = "PresBlue"
        self.in_votered_field = "PresRed"
        self.distcount = 7
        self.max_iter = 500
        self.temp = 20
        self.final_t = 0.1
        self.coolingrate = (self.final_t/self.temp)**(1/self.max_iter)
        self.tol = 30
        self.maxstopcounter = 50
        #self.alpha = [1, 1, 1, 1, 1]
        self.pop_perc = 15
        #self.naming_convention = "_Flip"
        self.num_maps = 6


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


def arcerror(message, *variables):
    '''
    Prints an error message using arcpy.AddError() unless it can't; then it
    uses print.
    '''
    if RUNSPOT == "ArcGIS":
        arcpy.AddError(message.format(*variables))
    elif RUNSPOT == "console":
        newmessage = message
        variables = list(variables)
        j = 0
        while j < len(variables):  #This while loop puts the variable(s) in the correct spot(s) in the string
            if isinstance(variables[j], float):
                variables[j] = round(variables[j], 3)
            newmessage = newmessage.replace("{"+str(j)+"}", str(variables[j]))  #Replaces {i} with the ith variable
            j=j+1
        raise RuntimeError(newmessage)
    else:
        raise RuntimeError("No value for RUNSPOT has been assigned")


def build_alpha(metric_count, num_maps):
    '''
    Builds the normalized weight vectors for use in simulated annealing
    '''
    alpha = [[0] * metric_count] * num_maps  #cols * rows
    for i in range(num_maps):
        for j in range(metric_count):
            alpha[i][j] = random.randint(1, 1000)
        tot = sum(alpha[i])
        for j in range(metric_count):
            alpha[i][j] = alpha[i][j]/tot
        eps = 0.000001
        if sum(alpha[i]) > 1 + eps or sum(alpha[i]) < 1 - eps:
            arcerror("The elements of alpha must sum to 1. alpha[{0}] = {1}",
                      i, alpha[i])
    return alpha


def initialize_map(ip,timetxt):
    """Generates an initial map using Spatially Constrained Multivariate Clustering"""
    #Counts number of rows in out_table      
    row_count = int(arcpy.GetCount_management(ip.in_table).getOutput(0)) #getOutput(0) returns the value at the first index position of a tool.
    
    #Creates name for the output map
    out_table = ip.in_table + "_SA" + "_{0}".format(ip.distcount) + "dists" + timetxt

    #Using Spatially Constrained Multivariate Clustering to create a random starting district
    if not arcpy.ListFields(ip.in_table, "Test_val"): #if field does not exist
        arcpy.AddField_management(ip.in_table, "Test_val","LONG",field_alias="Test_val")
        arcprint("Adding 'Test_val' field to in_table")
    with arcpy.da.UpdateCursor(ip.in_table, 'Test_val') as cursor:
        for row in cursor:
            row[0] = random.randint(1,100000)
            cursor.updateRow(row)
    arcprint("Running Spatially Constrained Multivariate Clustering to create the initial map...")
    
    mapflag = False
    failcount = 0
    while mapflag == False:
        try:
            arcpy.stats.SpatiallyConstrainedMultivariateClustering(ip.in_table,out_table, "Test_val",size_constraints="NUM_FEATURES", min_constraint=0.65*row_count/ip.distcount,  number_of_clusters=ip.distcount, spatial_constraints="CONTIGUITY_EDGES_ONLY")
            mapflag = True
        except arcpy.ExecuteError: #Occurs if SCMC cannot create a map with the given constraints
            arcprint("Attempt number {0} at using Spatially Constrained Multivariate Clustering (SCMC) failed. Trying again.", failcount)
            failcount = failcount +1
            if failcount >=21:
                arcerror("{0} attempts failed to produce a starting map for SCMC.",failcount)
            mapflag = False
            with arcpy.da.UpdateCursor(ip.in_table, 'Test_val') as cursor: #Resets the random values
                for row in cursor:
                    row[0] = random.randint(1,100000)
                    cursor.updateRow(row)
    
    
    #Adds populations as a column in out_table
    arcpy.management.JoinField(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_pop_field)
    
    #Adds vote totals as a column in out_table
    arcpy.management.JoinField(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_voteblue_field)
    arcpy.management.JoinField(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_votered_field)
    
    #Adds county numbers to out_table
    arcpy.management.JoinField(out_table, "SOURCE_ID", ip.in_table, ip.in_name_field, ip.in_county_field)
    return out_table

def main(*args):
    """ Runs the primary instance of the algorithm."""
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
    #arcpy.env.workspace = PATH
    arcpy.env.overwriteOutput = True

    #Get user input
    inputs = input_vals()
    ip = inputs #an alias
    sig = signature(input_vals.user_input)
    if len(sys.argv)==len(sig.parameters):
        arcprint("Using sys.argv")
        ip.user_input(sys.argv) #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
    elif len(args)==len(sig.parameters):
        arcprint("Using args")
        ip.user_input(args) #Second, tries to take input from explicit input into main()
    else:
        arcprint("Using default variable choices")
        ip.default_user_input() #Finally, manually assigns input values if they aren't provided

    #Marking the start time of the run.
    now = datetime.datetime.now()
    arcprint("Starting date and time : {0}",now.strftime("%d-%m-%y %H:%M:%S"))
    timetxt = now.strftime("_%m%d%y_%H%M")

    #This builds alpha, which is the normalized unit vector that details how much we care about any given metric.
    metric_count = 5
    alpha = build_alpha(metric_count, inputs.num_maps)
    
    tol = inputs.tol #tol will be modified later

    #Creates an initial map using Spatially Constrained Multivariate Clustering
    out_table = initialize_map(ip,timetxt)
    pass



if __name__ == "__main__":
    main()
