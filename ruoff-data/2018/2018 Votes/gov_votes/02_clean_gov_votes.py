# -*- coding: utf-8 -*-
## Script to clean county governor vote csv files before applying absentee vote splits
## Done in separate script because I'm not sure how to manipulate pandas dataframes...

## TO DO: DO THIS FOR EVERY FILE

import csv
import io
import os

county_vote_files = list()
for file in os.listdir('C:/Users/avagnoz/Desktop/Clemson_Redistricting_Team/ruoff-data/2018/2018 Votes/gov_votes'):
    if file.endswith('.csv'):
        county_vote_files.append(file)
assert(len(county_vote_files)==46)

for f in county_vote_files:
    filename = 'C:/Users/avagnoz/Desktop/Clemson_Redistricting_Team/ruoff-data/2018/2018 Votes/gov_votes/'+f

    infile = io.open(filename,newline='')
    reader = csv.reader(infile)
    # Rows 0 through 2 are headers.
    header = next(reader)
    header2 = next(reader)
    header3 = next(reader)
    # 0: Precinct, 1: Registered Voters, 3: DEM_Votes, 5: REP_Votes, 7: Write-In_Votes, 8: Total
    data = [[row[0], eval(row[1]), eval(row[3]), eval(row[5]), eval(row[7]), eval(row[8])] for row in reader]
    infile.close()
    
    # Add county column
    countyname = f[:-4]
    for row in data:
        row.insert(0,countyname)
        
    assert(data[-1][1]=='Total:')
    data.pop()
        
    outfile = open(filename,'w',newline='')
    writer = csv.writer(outfile)
    writer.writerow(['County','Precinct','Reg_Voters','DEM_Votes','REP_Votes','OTHER_Votes','Total'])
    for row in data:
        writer.writerow(row)
    outfile.close()
