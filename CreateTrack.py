import numpy as np
import matplotlib.pyplot as plt
from scipy.io import savemat

# Constants
straight_len = 1.364  # in meters (1364 mm)
curve_radius = 0.315  # in meters (315 mm)
num_points_straight = 100
num_points_curve = 100

# Top straight segment (top left to top right)
x1 = np.linspace(0, straight_len, num_points_straight)
y1 = np.zeros_like(x1)

# Right semicircle (top right to bottom right)
theta1 = np.linspace(-np.pi/2, np.pi/2, num_points_curve)
x2 = (straight_len) + curve_radius * np.cos(theta1)
y2 = curve_radius +  curve_radius * np.sin(theta1)

# Bottom straight segment (bottom right to bottom left)
x3 = np.linspace(0, straight_len, num_points_straight)
y3 = np.full_like(x3, 2 * curve_radius)

# Left semicircle (bottom left to top left)
theta2 = np.linspace(np.pi/2, 3*np.pi/2, num_points_curve)
x4 = curve_radius * np.cos(theta2)
y4 = curve_radius + curve_radius * np.sin(theta2)

# Combine
x_full = np.concatenate([x1, x2, x3, x4])
y_full = np.concatenate([y1, y2, y3, y4])
z_full = np.zeros_like(x_full)
r_full = np.vstack((x_full, y_full, z_full)).T

# Distance vector s
ds = np.sqrt(np.diff(x_full)**2 + np.diff(y_full)**2)
s = np.concatenate([[0], np.cumsum(ds)])

# Derivatives
drds = np.gradient(r_full, s, axis=0)
d2rds2 = np.gradient(drds, s, axis=0)

# Format tables
r_table = np.column_stack((s, r_full))
drds_table = np.column_stack((s, drds))
d2rds2_table = np.column_stack((s, d2rds2))

# Plot to visualize
plt.figure(figsize=(8, 4))
plt.plot(x_full, y_full, label='Flat Track')
plt.gca().set_aspect('equal')
plt.xlabel('X [m]')
plt.ylabel('Y [m]')
plt.title('Flat Track Visualizer')
plt.grid(True)
plt.legend()
plt.show()

# Save .mat file for Modelica
savemat('TrackTable.mat', {
    'r': r_table,
    'drds': drds_table,
    'd2rds2': d2rds2_table
})

