from fastkml import kml
from shapely.geometry import LineString
import numpy as np

with open("layer.kml", 'r') as f:
    doc = f.read()

k = kml.KML()
k.from_string(doc.encode('utf-8'))

# access nested features correctly
features = list(k.features)
if not features:
    raise RuntimeError("No features found in KML.")

document = list(features[0].features)
if not document:
    raise RuntimeError("No document features found in KML.")

placemark = list(document[0].features)
if not placemark:
    raise RuntimeError("No placemark features found in document.")

line: LineString = placemark[0].geometry

lonlat = np.array(line.coords)  # shape: (N, 3) → (lon, lat, alt)

