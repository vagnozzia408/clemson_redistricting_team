# -*- coding: utf-8 -*-
## Combines the votes in absentee_votes_allocated/ directory into one file.

import csv
import io
import os

county_vote_files = list()
for file in os.listdir('C:/Users/avagnoz/Desktop/Clemson_Redistricting_Team/ruoff-data/2018/2018 Votes/gov_votes/absentee_votes_allocated'):
    if file.endswith('.csv'):
        county_vote_files.append('C:/Users/avagnoz/Desktop/Clemson_Redistricting_Team/ruoff-data/2018/2018 Votes/gov_votes/absentee_votes_allocated/'+file)
assert(len(county_vote_files)==46)

all_precinct_data = []

total_DEM_votes = 0
total_REP_votes = 0
total_OTHR_votes = 0

for vote_file in county_vote_files:
	# Each vote_file is the filepath and filename of a file in the current directory.
	infile = io.open(vote_file, newline='')
	reader = csv.reader(infile)
	header = next(reader)
	data = [[row[0],row[1],eval(row[2]),eval(row[3]),eval(row[4]),eval(row[5])] for row in reader]
	infile.close()
		
	for row in data:
		all_precinct_data.append(row)
		total_DEM_votes += row[3]
		total_REP_votes += row[4]
		total_OTHR_votes += row[5]
		
	total_votes = total_DEM_votes + total_REP_votes + total_OTHR_votes
	DEM_share = total_DEM_votes / total_votes
	REP_share = total_REP_votes / total_votes
	OTHR_share = total_OTHR_votes / total_votes
		
outfile = open('C:/Users/avagnoz/Desktop/Clemson_Redistricting_Team/ruoff-data/2018/Governor_2018_Vote_Total_Summary.csv','w',newline='')
writer = csv.writer(outfile)
writer.writerow(["County","Precinct","Reg_Voters","DEM_Votes","REP_Votes","OTHR_Votes"])
for row in all_precinct_data:
	writer.writerow(row)
outfile.close()

print()
print("-------- SUMMARY --------")
print("Democratic Votes: " + str(int(total_DEM_votes)))
print("Republican Votes: " + str(int(total_REP_votes)))
print("Third Party Votes: " + str(int(total_OTHR_votes)))

print()
print("--- STATEWIDE SHARES ---")
print("Democratic Share: " + str(DEM_share * 100) + "%")
print("Republican Share: " + str(REP_share * 100) + "%")
print("Third Party Share: " + str(OTHR_share * 100) + "%")

print()
print("---- W/O THIRD PARTY ----")
print("Democratic Share: " + str(total_DEM_votes/(total_REP_votes+total_DEM_votes) *100) + "%")
print("Republican Share: " + str(total_REP_votes/(total_REP_votes+total_DEM_votes) *100) + "%")