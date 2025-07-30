import numpy as np
import matplotlib.pyplot as plt
from scipy.io import savemat

# Constants for the elliptical track
a = 24.0            # semi-major axis (m)
b =  8.0            # semi-minor axis (m)
num_points = 1000   # number of discrete points around the ellipse

# Parametric angle around ellipse
theta = np.linspace(0, 2*np.pi, num_points, endpoint=False)

# Coordinates of the ellipse
x_full = a * np.cos(theta)
y_full = b * np.sin(theta)
z_full = np.zeros_like(x_full)

# Stack into (N×3) array of positions
r_full = np.vstack((x_full, y_full, z_full)).T

# Compute cumulative distance s along the ellipse
#  (straight-line approximations between successive points, including wrap-around)
ds = np.sqrt(np.diff(x_full, append=x_full[0])**2 +
             np.diff(y_full, append=y_full[0])**2)
s = np.concatenate([[0], np.cumsum(ds)])  # length N+1; trim back to N
s = s[:num_points]

# Compute first & second derivatives dr/ds and d2r/ds2
drds   = np.gradient(r_full, s, axis=0)
d2rds2 = np.gradient(drds, s, axis=0)

# Build the tables
r_table      = np.column_stack((s,      r_full))
drds_table   = np.column_stack((s,      drds))
d2rds2_table = np.column_stack((s,      d2rds2))

# Plot to verify
plt.figure(figsize=(6,6))
plt.plot(x_full, y_full, '-', label=f'Ellipse Track (a={a}, b={b})')
plt.axis('equal')
plt.title(f'Elliptical Track, a={a} m, b={b} m, {num_points} points')
plt.xlabel('X [m]')
plt.ylabel('Y [m]')
plt.grid(True)
plt.legend()
plt.show()

# Save to .mat for Modelica
savemat('Digital/TrackTableCircle.mat', {
    'r':      r_table,
    'drds':   drds_table,
    'd2rds2': d2rds2_table
})
