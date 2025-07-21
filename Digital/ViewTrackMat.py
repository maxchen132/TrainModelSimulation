# run in jupyter notebook

import numpy as np
import pandas as pd
from scipy.io import loadmat

# 1. Load the .mat file
data = loadmat(r'C:\Users\mchen\Documents\Repositories\TrainModelSimulation\Digital\TrackTable.mat')

# 2. Extract arrays
r_array     = data['r']      # shape (N, 4): [s, x, y, z]
drds_array  = data['drds']   # shape (N, 4): [s, dr/ds]
d2rds2_array= data['d2rds2'] # shape (N, 4): [s, d2r/ds2]

# 3. Build DataFrames
df_r = pd.DataFrame(r_array, columns=['s [m]', 'x [m]', 'y [m]', 'z [m]'])
df_drds = pd.DataFrame(drds_array, columns=['s [m]', 'dx/ds', 'dy/ds', 'dz/ds'])
df_d2rds2 = pd.DataFrame(d2rds2_array, columns=['s [m]', 'd2x/ds2', 'd2y/ds2', 'd2z/ds2'])

# 4. Display every 10th row
display(df_r.iloc[::10, :])
display(df_drds.iloc[::10, :])
display(df_d2rds2.iloc[::10, :])
