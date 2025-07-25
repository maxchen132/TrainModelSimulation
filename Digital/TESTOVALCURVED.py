import numpy as np
import matplotlib.pyplot as plt
from scipy.io import savemat
from mpl_toolkits.mplot3d import Axes3D

# Constants
straight_len = 100  # in meters (1364 mm)
curve_radius = 10  # in meters (315 mm)
num_points_straight = 100
num_points_curve = 100

# bottom straight segment (top left to top right)
theta1 = np.linspace(-np.pi, 0, num_points_curve)
x1 = (straight_len/2) + (straight_len/2)* np.cos(theta1)
y1 = curve_radius/10 * np.sin(theta1)

# right semi circle
theta2 = np.linspace(-np.pi/2, np.pi/2, num_points_curve)
x2 = (straight_len) + curve_radius * np.cos(theta2)
y2 = curve_radius +  curve_radius * np.sin(theta2)

# Remove duplicate point
x2 = x2[1:]
y2 = y2[1:]

# top straight
theta3 = np.linspace(0, np.pi, num_points_curve)
x3 = (straight_len/2) + (straight_len/2)* np.cos(theta3)
y3 = curve_radius*2 + curve_radius/10 * np.sin(theta3)

# Remove duplicate point
x3 = x3[1:]
y3 = y3[1:]

# Left semicircle (bottom left to top left)
theta4 = np.linspace(np.pi/2, 3*np.pi/2, num_points_curve)
x4 = curve_radius * np.cos(theta4)
y4 = curve_radius + curve_radius * np.sin(theta4)

# Remove duplicate point
x4 = x4[1:]
y4 = y4[1:]
# Combine
x_full = np.concatenate([x1, x2, x3, x4])
y_full = np.concatenate([y1, y2, y3, y4])
z_full = np.zeros_like(x_full)
r_full = np.vstack((x_full, y_full, z_full)).T

# Remove near-duplicate points (too small distance between them)
eps = 1e-8
dx = np.diff(x_full)
dy = np.diff(y_full)
dist = np.sqrt(dx**2 + dy**2)
mask = np.concatenate(([True], dist > eps))  # keep first, then only if distance is big enough
x_full = x_full[mask]
y_full = y_full[mask]

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
plt.figure(figsize=(8, 6))
plt.plot(x_full, y_full, label='Flat Track')

# add arrows to indicate direction
for i in range(0, len(x_full) - 1, 10):  # adjust step size for density
    dx = x_full[i+1] - x_full[i]
    dy = y_full[i+1] - y_full[i]
    plt.arrow(x_full[i], y_full[i], dx, dy,
              shape='full', head_width=2, head_length=1, color='red')

plt.gca().set_aspect('equal')
plt.xlabel('X [m]')
plt.ylabel('Y [m]')
plt.title('Flat Track Visualizer with Direction')
plt.grid(True)
plt.legend()
plt.show()


# Save .mat file for Modelica
savemat('TrackTable.mat', {
    'r': r_table,
    'drds': drds_table,
    'd2rds2': d2rds2_table
})


