# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 15:28:25 2021

@author: blake
"""


import arcpy,numpy
 
# Set environment settings
path = r"C:\Users\blake\Documents\Clemson Materials\Research\Saltzman Research\clemson_redistricting_team\SC_Redistricting_Updated\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path

in_table="tl_2020_45_county20"
#fieldName = "Test_val"
#expression = 'numpy.random.randint(1,7)'

#arcpy.CalculateField_management(in_table, fieldName, expression, "PYTHON3")


with arcpy.da.UpdateCursor(in_table, ['SUM_Popula','Test_val']) as cursor:
    for row in cursor:
        row[1] = numpy.random.randint(1,8)
        cursor.updateRow(row)
        
