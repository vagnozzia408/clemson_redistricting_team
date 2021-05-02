# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 16:57:08 2021

@author: blake
"""

"The goal of this code is to create a random contiguous districting on the polygons given as input"

import arcpy, numpy

# Set property to overwrite existing output, by default
arcpy.env.overwriteOutput = True

# Set environment settings
path = r"C:\Users\blake\Documents\Clemson Materials\Research\Saltzman Research\clemson_redistricting_team\SC_Redistricting_Updated\SC_Redistricting_Updated.gdb"
arcpy.env.workspace = path



in_table = arcpy.GetParameterAsText(0)

with arcpy.da.UpdateCursor(in_table, 'Test_val') as cursor:
    for row in cursor:
        row[0] = numpy.random.randint(100)
        cursor.updateRow(row)

arcpy.stats.SpatiallyConstrainedMultivariateClustering(in_table,"out_table","Test_val","ATTRIBUTE_VALUE","SUM_Popula",300000,None,7,"CONTIGUITY_EDGES_ONLY")
