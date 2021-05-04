# -*- coding: utf-8 -*-
"""
Created on Mon May  3 19:30:31 2021

@author: blake
"""


import arcpy

p = arcpy.mp.ArcGISProject("CURRENT")
m = p.listMaps('Map')[0]
lyr = m.listLayers("SC_Counties_2020_RandomDistricting")[0]
sym = lyr.symbology
#sym.updateRenderer('UniqueValueRenderer')
#sym.renderer.fields = ["Test_val"]
#sym.renderer.addAllValues()
if hasattr(sym, 'renderer'):
    sym.updateRenderer('UniqueValueRenderer')
    sym.renderer.fields = ['CLUSTER_ID']
lyr.symbology = sym


# if my_lyr.symbologyType == "UNIQUE_VALUES":
#     my_lyr.symbology.valueField = "Test_val"
#     my_lyr.symbology.addAllValues()
# arcpy.RefreshActiveView()
# arcpy.RefreshTOC()