import pyproj

# define projection: WGS84 (lat/lon) → UTM or local meter system
proj = pyproj.Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)  # Web Mercator meters

x, y = proj.transform(lonlat[:, 0], lonlat[:, 1])

