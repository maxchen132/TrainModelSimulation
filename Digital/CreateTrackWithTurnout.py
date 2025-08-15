import numpy as np
import matplotlib.pyplot as plt
from scipy.io import savemat

# --- PARAMETERS ---
straight_len     = 136   # bottom straight length [m]
curve_radius     = 31    # semicircle radius [m]
num_pts_straight = 100
num_pts_curve    = 100

branch_offset    = 5.0   # lateral offset [m]
parallel_length  = 130  # length of the straight, offset section [m]
fillet_pts       = 20    # points per curved transition

# --- 1) Build full bottom straight (westbound) ---
x_full = np.linspace(straight_len, 0, num_pts_straight)[1:]
y_full = np.full_like(x_full, 2*curve_radius)

# --- 2) Compute cumulative s, find split indices ---
ds3 = np.hypot(np.diff(x_full), np.diff(y_full))
s3  = np.concatenate([[0], np.cumsum(ds3)])
total_len = s3[-1]

s_start = (total_len - parallel_length)/2
s_end   = (total_len + parallel_length)/2
i_start = np.searchsorted(s3, s_start)
i_end   = np.searchsorted(s3, s_end)

# Pre, mid, post
x_pre,  y_pre  = x_full[:i_start],        y_full[:i_start]
x_mid,  y_mid  = x_full[i_start:i_end],   y_full[i_start:i_end]
x_post, y_post = x_full[i_end:],          y_full[i_end:]

mid_count = len(x_mid)
# Make sure we have room for two fillets:
max_fillet = mid_count // 2
# Choose the smaller of your desired fillet_pts and what will fit
fillet_pts = min(fillet_pts, max_fillet)

# Now recompute your half‐cosine deltas
theta      = np.linspace(0, np.pi, fillet_pts)
delta_div  = branch_offset * (1 - np.cos(theta)) / 2
delta_conv = branch_offset * (1 + np.cos(theta)) / 2


# --- 3) Define the two fillet curves (half‐cosine ramps) ---
# Diverging: from offset=0 → branch_offset
theta = np.linspace(0, np.pi, fillet_pts)
delta_div  = branch_offset*(1 - np.cos(theta))/2
# Converging: from offset=branch_offset → 0
delta_conv = branch_offset*(1 + np.cos(theta))/2

# Map these onto X along the beginning and end of the mid‐segment
x_div = x_mid[:fillet_pts]
x_conv = x_mid[-fillet_pts:]

y_div = y_mid[:fillet_pts] + delta_div
y_const = y_mid[fillet_pts:-fillet_pts] + branch_offset
y_conv = y_mid[-fillet_pts:] + delta_conv

# --- 4) Assemble branch X,Y in order ---
x_branch = np.concatenate([ x_pre,
                            x_div,
                            x_mid[fillet_pts:-fillet_pts],
                            x_conv,
                            x_post ])
y_branch = np.concatenate([ y_pre,
                            y_div,
                            y_const,
                            y_conv,
                            y_post ])

# --- 5) Build a helper to wrap into the full stadium track ---
def build_loop(xb, yb):
    # top straight
    xs = np.linspace(0, straight_len, num_pts_straight)[1:];  ys = np.zeros_like(xs)
    # right curve
    th1 = np.linspace(-np.pi/2, np.pi/2, num_pts_curve)[1:]
    xr = straight_len + curve_radius*np.cos(th1)
    yr = curve_radius   + curve_radius*np.sin(th1)
    # left curve
    th2 = np.linspace(np.pi/2, 3*np.pi/2, num_pts_curve)[1:]
    xl = curve_radius*np.cos(th2)
    yl = curve_radius   + curve_radius*np.sin(th2)

    x = np.concatenate([xs, xr, xb, xl])
    y = np.concatenate([ys, yr, yb, yl])
    # prune near-duplicate
    d = np.hypot(np.diff(x), np.diff(y))
    mask = np.concatenate([[True], d>1e-8])
    x, y = x[mask], y[mask]
    # build r, s, drds, d2rds2
    z = np.zeros_like(x)
    r = np.vstack((x,y,z)).T
    ds = np.hypot(np.diff(x,append=x[0]), np.diff(y,append=y[0]))
    s = np.concatenate([[0], np.cumsum(ds)])[:len(x)]
    drds   = np.gradient(r, s, axis=0)
    d2r    = np.gradient(drds, s, axis=0)
    perimeter = ds.sum()
    return s, r, drds, d2r, perimeter

# Main vs branch
s_main,   r_main,   drds_main,   d2r_main, s_main_len   = build_loop(x_full,  y_full)
s_branch, r_branch, drds_branch, d2r_branch, s_branch_len = build_loop(x_branch, y_branch)

# Format tables
r_table_main = np.column_stack((s_main, r_main))
drds_table_main = np.column_stack((s_main, drds_main))
d2rds2_table_main = np.column_stack((s_main, d2r_main))
r_table_branch = np.column_stack((s_branch, r_branch))
drds_table_branch = np.column_stack((s_branch, drds_branch))
d2rds2_table_branch = np.column_stack((s_branch, d2r_branch))

# --- 6) Save to MAT (or CSV) ---
savemat('Digital/TurnoutTable.mat',{
  'r_main':r_table_main,    'drds_main':drds_table_main,    'd2rds2_main':d2rds2_table_main,
  'r_branch':r_table_branch,'drds_branch':drds_table_branch,'d2rds2_branch':d2rds2_table_branch
})

with open('Digital/last_s.txt', 'w') as output:
    output.write(str(s_main_len) + "\n")

with open('Digital/last_s.txt', 'a') as output:
    output.write(str(s_branch_len))

# --- 7) Quick plot check ---
plt.figure(figsize=(6,6))
plt.plot(r_main[:,0],   r_main[:,1],   '-b', label='Mainline')
plt.plot(r_branch[:,0], r_branch[:,1], '--r',label='Branch')
plt.axis('equal'); plt.grid(); plt.legend(); plt.title("Rounded Turnout, Both Sides")
plt.show()