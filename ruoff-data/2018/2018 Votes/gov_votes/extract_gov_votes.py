# -*- coding: utf-8 -*-
## Working on script to extract governor vote totals from the 2018 general election.
## Could be modified to extract votes from any election

## To Do Items:
    # Make filepaths relative (not just for my filesystem)
    # Clean the csv files that get exported

import pandas as pd #used to manipulate excel files
import os #used to access the directory list

#save filenames of each county vote spreadsheets (xlsx) in a list
county_vote_files = list()
for file in os.listdir('C:/Users/avagnoz/Desktop/Clemson_Redistricting_Team/ruoff-data/2018/2018 Votes'):
    if file.endswith('.xlsx'):
        county_vote_files.append(file)
assert(len(county_vote_files)==46)

for f in county_vote_files:
    filename = 'C:/Users/avagnoz/Desktop/Clemson_Redistricting_Team/ruoff-data/2018/2018 Votes/'+f
    read_file = pd.read_excel(filename,sheet_name = '3')
    county = f[:-5]
    new_csv = 'C:/Users/avagnoz/Desktop/Clemson_Redistricting_Team/ruoff-data/2018/2018 Votes/gov_votes/'+county+'.csv'
    read_file.to_csv (new_csv, index=None, header=True)
