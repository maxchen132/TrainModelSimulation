# mirror_sensors_startup.py
# JMRI Jython script
#
# Mirrors source sensors MS4..MS14 into internal sensors IS1..IS12, skipping IS4
# on startup, and keeps them synchronized afterward.


import jmri
from java.beans import PropertyChangeListener

MAPPINGS = [
    ("IS1",  "MS4"),
    ("IS2",  "MS5"),
    ("IS3",  "MS6"),
    ("IS5",  "MS7"),
    ("IS6",  "MS8"),
    ("IS7",  "MS9"),
    ("IS8",  "MS10"),
    ("IS9",  "MS11"),
    ("IS10",  "MS12"),
    ("IS11", "MS13"),
    ("IS12", "MS14"),
]

# Keep references so listeners are not garbage-collected.
_listeners = []

class MirrorListener(PropertyChangeListener):
    def __init__(self, target_sensor):
        self.target_sensor = target_sensor

    def propertyChange(self, event):
        if event.propertyName == "KnownState":
            self.target_sensor.setKnownState(event.newValue)

def sync_pair(target_name, source_name):
    target = sensors.provideSensor(target_name)
    source = sensors.provideSensor(source_name)

    # Copy current state at startup
    target.setKnownState(source.getKnownState())

    # Keep target synced with source after startup
    listener = MirrorListener(target)
    source.addPropertyChangeListener(listener)
    _listeners.append(listener)

for target_name, source_name in MAPPINGS:
    sync_pair(target_name, source_name)

print("Sensor mirror initialized for {} pairs.".format(len(MAPPINGS)))