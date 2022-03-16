import Many_map_creation
import numpy
import pandas as pd

my_file = r"C:\Users\blake\OneDrive - Clemson University\Documents\Research\clemson_redistricting_team\SC_Redistricting_Updated\Many_map_creation.py"
iterations = 50
ov = [0] * iterations
missed_its = []
for i in range(iterations):
    try:
        ov[i] = Many_map_creation.main(1, i)
    except ValueError:
        missed_its.append(i)
        pass

pop_list = []
comp_list = []
cdi_list = []
egu_list = []
eg_list = []
mm_list = []
for i in range(iterations):
    if i in missed_its: continue
    pop_list.append(ov[i].dev_vals)
    comp_list.append(ov[i].avg_comp_vals)
    eg_list.append(ov[i].eg_score_vals)
    cdi_list.append(ov[i].CDI_Count_vals)
    egu_list.append(ov[i].excess_GU_vals)
    mm_list.append(ov[i].mm_vals)

pop_std = numpy.std(pop_list)
comp_std = numpy.std(comp_list)
eg_std = numpy.std(eg_list)
cdi_std = numpy.std(cdi_list)
egu_std = numpy.std(egu_list)
mm_std = numpy.std(mm_list)

data_table = [[pop_std, comp_std, eg_std, cdi_std, egu_std, mm_std]]
df = pd.DataFrame(data_table, columns = ["Population std", "Compactness std", "Efficiency Gap std", "CDI std", "excess_GU std", "mm std"])
print(df)
print("finished!")
