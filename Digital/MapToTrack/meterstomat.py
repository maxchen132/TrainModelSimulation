from scipy.io import savemat

z = np.zeros_like(x)
r_full = np.vstack((x, y, z)).T

# Arc length
ds = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
s = np.concatenate([[0], np.cumsum(ds)])

# Derivatives
drds = np.gradient(r_full, s, axis=0)
d2rds2 = np.gradient(drds, s, axis=0)

# Save
savemat('TrackTable.mat', {
    'r': np.column_stack((s, r_full)),
    'drds': np.column_stack((s, drds)),
    'd2rds2': np.column_stack((s, d2rds2)),
})

