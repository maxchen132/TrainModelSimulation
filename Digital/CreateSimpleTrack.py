import numpy as np
import matplotlib.pyplot as plt
from scipy.io import savemat

# Constants
straight_len = 10  # in meters (1364 mm)
curve_radius = 50  # in meters (315 mm)
num_points_straight = 50
num_points_curve = 100

# Top straight segment (top left to top right)
x1 = np.linspace(0, straight_len, num_points_straight)
y1 = np.zeros_like(x1)

# Right semicircle (top right to bottom right)
theta1 = np.linspace(-np.pi/2, 0, num_points_curve)
x2 = curve_radius * np.cos(theta1)
y2 = curve_radius +  curve_radius * np.sin(theta1)

# Get rid of duplicate point
x2 = x2[1:]
y2 = y2[1:]

theta2 = np.linspace(-np.pi, -(3*np.pi/2), num_points_curve)
x3 = 2 * curve_radius + curve_radius * np.cos(theta2)
y3 = curve_radius +  curve_radius/1000 * np.sin(theta2)



# Combine
x_full = np.concatenate([x2, x3])
y_full = np.concatenate([y2, y3])

# Remove duplicate points if any
eps = 1e-6
dx = np.diff(x_full)
dy = np.diff(y_full)
distances = np.sqrt(dx**2 + dy**2)
mask = np.concatenate(([True], distances > eps))

x_full = x_full[mask]
y_full = y_full[mask]

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

savemat('Digital/TrackTableSimple.mat', {
    'r': r_table,
    'drds': drds_table,
    'd2rds2': d2rds2_table
})


# Plot to visualize
fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(x_full, y_full, label='Flat Track')


for i in range(0, len(x_full) - 1, 10):  # adjust step size for density
    dx = x_full[i+1] - x_full[i]
    dy = y_full[i+1] - y_full[i]
    plt.arrow(x_full[i], y_full[i], dx, dy,
              shape='full', head_width=2, head_length=1, color='red')


# direction arrows
ax.set_xlabel('X [m]')
ax.set_ylabel('Y [m]')
ax.set_title('2D Flat Track Visualizer with Direction')
plt.legend()
plt.show()
