import numpy as np
import matplotlib.pyplot as plt
from scipy.io import loadmat
import sys

# Optional: pass the filename as a command line argument
if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = 'TrackTable.mat'  # fallback default

# Load .mat file
data = loadmat(filename)

# Extract positions (r = [s, x, y, z])
r_array = data['r']  # shape (N, 4)
s = r_array[:, 0]
x = r_array[:, 1]
y = r_array[:, 2]

# Visualize
fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(x, y, label='Track')

# Draw direction arrows
for i in range(0, len(x) - 1, 10):
    dx = x[i+1] - x[i]
    dy = y[i+1] - y[i]
    ax.arrow(x[i], y[i], dx, dy,
             shape='full', head_width=2, head_length=1, color='red')

ax.set_xlabel('X [m]')
ax.set_ylabel('Y [m]')
ax.set_title(f'Track Visualizer: {filename}')
ax.legend()
plt.axis('equal')
plt.tight_layout()
plt.show()


