# -*- coding: utf-8 -*-
## Splits absentee votes proportionally by percentage of registered voters per precinct.
## Borrowed code from absenteesplit2010.py written for thesis work (can be found on external hard drive)

import os
import io
import csv

#Checks rows to determine if we're looking at one of the virtual precincts.
def check_pct_keywords(pct):
    """A method for checking to see whether or not a precinct falls into one
    of the following categories of 'virtual' precincts."""
    pct_keyword = ['absentee', 'emergency', 'failsafe', 'provisional']
    search_result = False
    for word in pct_keyword:
        if word in pct:
            search_result = True
            break
    return search_result

#Do this for every vote file in the directory
county_vote_files = list()
for file in os.listdir('C:/Users/avagnoz/Desktop/Clemson_Redistricting_Team/ruoff-data/2018/2018 Votes/gov_votes'):
    if file.endswith('.csv'):
        county_vote_files.append('C:/Users/avagnoz/Desktop/Clemson_Redistricting_Team/ruoff-data/2018/2018 Votes/gov_votes/'+file)
assert(len(county_vote_files)==46)

for file in county_vote_files:
    #Read in the County CSV
    infile = io.open(file,newline='')
    reader = csv.reader(infile)
    header = next(reader)
    # 0: County, 1: Precinct, 2: Reg_Voters, 3: DEM_Votes, 4: REP_Votes, 5: OTHER_Votes
    data = [[row[0],row[1],eval(row[2]),eval(row[3]),eval(row[4]),eval(row[5])] for row in reader]
    infile.close()
    
    ###### SPLIT ABSENTEE VOTES #######
    # Initialize variables...
    total_reg_voters = 0
    
    unallocated_REP_votes = 0
    unallocated_DEM_votes = 0
    unallocated_OTHER_votes = 0
    
    idx = []
    
    for line in data:
        # Add virtual precinct votes to the unallocated vote counts for each party.
        if check_pct_keywords(line[1].lower()):
            unallocated_DEM_votes += line[3]
            unallocated_REP_votes += line[4]
            unallocated_OTHER_votes += line[5]
            
            # Store row indices of virtual precincts to delete.
            idx.append(data.index(line))
            
        # Otherwise, sum up the total number of registered voters.
        # Virtual precincts have '0' registered voters and don't need to be counted.
        else:
            total_reg_voters += line[2]
            
    # Once we've counted the unallocated votes, we can delete the virtual precincts.
    for i in reversed(idx):
        del data[i]   
        
    # Allocate the virtual precinct votes proportionally by registered voters.
    for line in data:
        if check_pct_keywords(line[1].lower())==True:
            break
        else:
            percent_reg_voters = line[2]/total_reg_voters
            
            DEM_votes_to_add = percent_reg_voters * unallocated_DEM_votes
            REP_votes_to_add = percent_reg_voters * unallocated_REP_votes
            OTHER_votes_to_add = percent_reg_voters * unallocated_OTHER_votes
            
            line[3] += DEM_votes_to_add
            line[4] += REP_votes_to_add
            line[5] += OTHER_votes_to_add
    
    # Store data...
    newfilename = 'C:/Users/avagnoz/Desktop/Clemson_Redistricting_Team/ruoff-data/2018/2018 Votes/gov_votes/absentee_votes_allocated/'+file[89:]
    outfile = open(newfilename, 'w', newline='')
    writer = csv.writer(outfile)
    
    # Write the header.
    writer.writerow(["County","Precinct","Reg_Voters","DEM_Votes","REP_Votes","OTHER_Votes"])
    
    for row in data:
        writer.writerow(row)
    
    outfile.close()