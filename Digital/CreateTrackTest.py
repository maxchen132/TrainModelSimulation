import numpy as np
import matplotlib.pyplot as plt
from scipy.io import savemat

# Parameters
curve_radius = 31  # meters
straight_len = 136  # meters
num_points_curve = 500
num_points_straight = 500

#theta1 = np.linspace(-np.pi + 1, -1, num_points_curve)
#x1 = (straight_len/2) + (straight_len/2) * np.cos(theta1)
#y1 = curve_radius/10 * np.sin(theta1)
x1 = np.linspace(0, straight_len, num_points_straight)
y1 = np.zeros_like(x1)

x1 = x1[1:]
y1 = y1[1:]

# right semi circle
theta2 = np.linspace(-np.pi/2, 0, num_points_curve)
x2 = (straight_len) + curve_radius * np.cos(theta2)
y2 = curve_radius +  curve_radius * np.sin(theta2)

# Remove duplicate point
x2 = x2[1:]
y2 = y2[1:]


y5 = np.linspace(curve_radius, straight_len, num_points_straight)
x5 = straight_len + curve_radius + np.zeros_like(y5)

x5 = x5[1:]
y5 = y5[1:]



x3 = np.linspace(straight_len, 0, num_points_straight)
y3 = curve_radius*2 + np.zeros_like(x3)

x3 = x3[1:]
y3 = y3[1:]

# right semi circle
theta4 = np.linspace(3*np.pi/2, np.pi/2, num_points_curve)
x4 = (straight_len) + curve_radius * np.cos(theta4)
y4 = 3*curve_radius +  curve_radius * np.sin(theta4)

# Remove duplicate point
x2 = x2[1:]
y2 = y2[1:]
#theta2 = np.linspace(-np.pi, -(4*np.pi/2), num_points_curve)
#x2 = 2 * curve_radius + curve_radius * np.cos(theta2)
#y2 = curve_radius +  curve_radius/5 * np.sin(theta2)

#x2 = x2[1:]
#y2 = y2[1:]

#theta3 = np.linspace(-np.pi, -np.pi/2, num_points_curve)
#x3 = 200 + curve_radius * np.cos(theta3)
#y3 = curve_radius + curve_radius * np.sin(theta3)

# Combine
x_full = np.concatenate([x5])
y_full = np.concatenate([y5])

# Remove near-duplicate points (too small distance between them)
eps = 1e-8
dx = np.diff(x_full)
dy = np.diff(y_full)
dist = np.sqrt(dx**2 + dy**2)
mask = np.concatenate(([True], dist > eps))  # keep first, then only if distance is big enough
x_full = x_full[mask]
y_full = y_full[mask]

# 3D track data
z_full = np.zeros_like(x_full)
r_full = np.vstack((x_full, y_full, z_full)).T

# Arc length s
ds = np.sqrt(np.diff(x_full)**2 + np.diff(y_full)**2)
s = np.concatenate([[0], np.cumsum(ds)])

# Derivatives
drds = np.gradient(r_full, s, axis=0)
d2rds2 = np.gradient(drds, s, axis=0)

# Format for .mat export
r_table = np.column_stack((s, r_full))
drds_table = np.column_stack((s, drds))
d2rds2_table = np.column_stack((s, d2rds2))

# Save to .mat
savemat('TrackTable.mat', {
    'r': r_table,
    'drds': drds_table,
    'd2rds2': d2rds2_table
})

# Plot
fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(x_full, y_full, label='Flat Track')

for i in range(0, len(x_full) - 1, 10):
    dx = x_full[i+1] - x_full[i]
    dy = y_full[i+1] - y_full[i]
    plt.arrow(x_full[i], y_full[i], dx, dy,
              shape='full', head_width=2, head_length=1, color='red')

ax.set_xlabel('X [m]')
ax.set_ylabel('Y [m]')
ax.set_title('2D Flat Track Visualizer with Direction')
plt.legend()
plt.show()

