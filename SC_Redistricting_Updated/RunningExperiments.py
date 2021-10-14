# -*- coding: utf-8 -*-
"""
Created on Fri Oct  8 09:38:52 2021

@author: aburt
"""

import arcpy,os,sys
import random
seed = 1738
random.seed(seed)
import MultiCriteriaSimulatedAnnealing
import datetime

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

class Experiment:
    alpha = []
    out_table_NAME = ""
    now = -1
    startPopDev = -1
    endPopDev = -1
    avgcompStart = -1
    avgcompEnd = -1
    r_fairscoreStart = -1
    r_fairscoreEnd = -1
    CDI_Count_valsStart = -1
    CDI_Count_valsEnd = -1
    CDI_Square_valsStart = -1
    CDI_Square_valsEnd = -1
    sumpop = []
    compactscores = []
    info_file = 0
        
    def __init__(self, alph, name):
        self.alpha = alph
        self.out_table_NAME = name
        self.now = -1
        self.startPopDev = -1
        self.endPopDev = -1
        self.avgcompStart = -1
        self.avgcompEnd = -1
        self.r_fairscoreStart = -1
        self.r_fairscoreEnd = -1
        self.CDI_Count_valsStart = -1
        self.CDI_Count_valsEnd = -1
        self.CDI_Square_valsStart = -1
        self.CDI_Square_valsEnd = -1
        self.sumpop = []
        self.compactscores = []
    
    def StoreStats(self, n, spd, epd, acs, ace, fss, fse, cdicvs, cdicve, cdisvs, cdisve, sp, cp):
        self.now = n
        self.startPopDev = spd
        self.endPopDev = epd
        self.avgcompStart = acs
        self.avgcompEnd = ace
        self.r_fairscoreStart = fss
        self.r_fairscoreEnd = fse
        self.CDI_Count_valsStart = cdicvs
        self.CDI_Count_valsEnd = cdicve
        self.CDI_Square_valsStart = cdisvs
        self.CDI_Square_valsEnd = cdisve
        self.sumpop = sp
        self.compactscores = cp

def main(*args):
    global runspot #Allows runspot to be changed inside a function
    
    if sys.executable == r"C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe": #Change this line if ArcGIS is located elsewhere
        runspot = "ArcGIS"
    else:
        runspot = "console"
            
    # Set environment settings
    global currentdir
    global path
    
    currentdir = os.getcwd()
    path = currentdir + "\\SC_Redistricting_Updated.gdb"
    arcpy.env.workspace = path
    
    arcpy.env.overwriteOutput = True
    
    global coolingrate
    
    try: #First attempts to take input from system arguments (Works for ArcGIS parameters, for instance)
        in_table = sys.argv[1]
        in_pop_field = sys.argv[2]
        in_name_field = sys.argv[3]
        distcount = int(sys.argv[4])
        MaxIter = int(sys.argv[5])
        T = float(sys.argv[6])
        FinalT = float(sys.argv[7])
        coolingrate = (FinalT/T)**(1/MaxIter)
        tol = float(sys.argv[8])
        maxstopcounter = sys.argv[9]
        numExperiments = sys.argv[10]
    except IndexError: 
        try: #Second, tries to take input from explicit input into main()
            in_table = args[0]
            in_pop_field = args[1]
            in_name_field = args[2]
            distcount = int(args[3])
            MaxIter = int(args[4])
            T = float(args[5])
            FinalT = float(args[6])
            coolingrate = (FinalT/T)**(1/MaxIter)
            tol = float(args[7])
            maxstopcounter = args[8]
            numExperiments = args[9]
        except IndexError: #Finally, manually assigns input values if they aren't provided
#            in_table=path+"\\tl_2020_45_county20_SpatiallyConstrainedMultivariateClustering1"
#            in_pop_field = "SUM_Popula"
#            in_name_field = "OBJECTID"
            in_table = path + "\\Precincts_2020"
            in_pop_field = "Precinct_P"
            in_name_field = "OBJECTID_1"
            distcount=7
            MaxIter=100
            T = 20
            FinalT = 0.1
            coolingrate = (FinalT/T)**(1/MaxIter)
            tol=30
            maxstopcounter=50
            numExperiments = 2
            arcprint("We are using default input choices")
     
    StartTime = datetime.datetime.now()
    arcprint("Starting date and time : {0}",StartTime.strftime("%Y-%m-%d %H:%M:%S"))
    global ExperimentHolder
    ExperimentHolder = list(range(numExperiments))
    ExperimentHolder[0] = Experiment([1, 0, 0, 0, 0], "_10000")
    ExperimentHolder[1] = Experiment([0.75, 1, 0, 0, 0], "_01000")
    
    for ex in ExperimentHolder:
        [n, spd, epd, acs, ace, fss, fse, cdicvs, cdicve, cdisvs, cdisvek, sp, cp] = MultiCriteriaSimulatedAnnealing.main(in_table,in_pop_field,in_name_field,distcount,MaxIter,T,FinalT,tol,maxstopcounter,ex.alpha.copy(),ex.out_table_NAME)
        ex.StoreStats(n, spd, epd, acs, ace, fss, fse, cdicvs, cdicve, cdisvs, cdisvek, sp, cp)
        arcprint("FINISHED ANOTHER EXPERIMENT!")
         
    EndTime = datetime.datetime.now()
    arcprint("Full Run Lasted : {0} -- {1}",StartTime.strftime("%Y-%m-%d %H:%M:%S"), EndTime.strftime("%Y-%m-%d %H:%M:%S"))
    
    
    
            
#END FUNCTIONS    
if __name__ == "__main__":
    main()