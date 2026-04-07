import csv
import json
import os
import socket
import jmri
from datetime import datetime
from java.beans import PropertyChangeListener
from java.awt.event import ActionListener
from javax.swing import Timer as SwingTimer

# Network config
with open("/home/wayside/Downloads/JMRI.5.10+Rca461bd266/JMRI/network_config.json") as f:
    config = json.load(f)

UDP_IP = config["broadcast_ip"]
UDP_PORT = config["port"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

print("Network configured: {}:{}".format(UDP_IP, UDP_PORT))

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

# Turnouts — DT500 through DT570
TURNOUT_IDS = ["DT500", "DT510", "DT520", "DT530", "DT540", "DT550", "DT560", "DT570"]

turnout_objects = {}
for tid in TURNOUT_IDS:
    t = turnouts.provideTurnout(tid)
    turnout_objects[tid] = t
    print("  Registered turnout: {}".format(tid))

# Sensors — IS1-IS12 (virtual, mirrored from real MS sensors)
SENSOR_IDS = ["IS1", "IS2", "IS3", "IS5", "IS6", "IS7", "IS8", "IS9", "IS10", "IS11", "IS12"]

sensor_objects = {}
for sid in SENSOR_IDS:
    s = sensors.provideSensor(sid)
    sensor_objects[sid] = s
    print("  Registered sensor: {}".format(sid))

# Broadcast current full state over UDP
def broadcast_state(reason="periodic"):
    data = {
        "timestamp": get_timestamp(),
        "reason": reason,
        "turnouts": {},
        "sensors": {}
    }

    for tid, t in turnout_objects.items():
        state = t.getCommandedState()
        data["turnouts"][tid] = "THROWN" if state == jmri.Turnout.THROWN else "CLOSED"

    for sid, s in sensor_objects.items():
        state = s.getKnownState()
        if state == jmri.Sensor.ACTIVE:
            data["sensors"][sid] = "OCCUPIED"
        elif state == jmri.Sensor.INACTIVE:
            data["sensors"][sid] = "UNOCCUPIED"
        else:
            data["sensors"][sid] = "UNKNOWN"

    json_data = json.dumps(data)
    sock.sendto(json_data.encode(), (UDP_IP, UDP_PORT))

# Milliseconds a sensor state must be stable before being recorded
SENSOR_DEBOUNCE_MS = 300

# Active debounce timers keyed by sensor_id
_sensor_debounce_timers = {}

# Listeners — keep references to prevent garbage collection
_listeners = []

# --- Turnout change listener ---
class TurnoutChangeListener(PropertyChangeListener):
    def __init__(self, turnout_id):
        self.turnout_id = turnout_id

    def propertyChange(self, event):
        if event.propertyName == "CommandedState":
            state = "THROWN" if event.newValue == jmri.Turnout.THROWN else "CLOSED"
            print("[{}] TURNOUT {} changed to {}".format(
                get_timestamp(), self.turnout_id, state))
            broadcast_state(reason="turnout_change_" + self.turnout_id)

for tid, t in turnout_objects.items():
    listener = TurnoutChangeListener(tid)
    t.addPropertyChangeListener(listener)
    _listeners.append(listener)

# --- Sensor change listener (with debounce) ---
class SensorDebounceAction(ActionListener):
    def __init__(self, sensor_id, expected_state):
        self.sensor_id = sensor_id
        self.expected_state = expected_state

    def actionPerformed(self, event):
        # Only commit if the sensor is still in the expected state after the delay
        current_state = sensor_state_to_text(sensor_objects[self.sensor_id])
        if current_state == self.expected_state:
            print("[{}] SENSOR Block/Sensor {} {}".format(
                get_timestamp(), self.sensor_id, current_state))
            broadcast_state(reason="sensor_change_" + self.sensor_id)
        _sensor_debounce_timers.pop(self.sensor_id, None)


class SensorChangeListener(PropertyChangeListener):
    def __init__(self, sensor_id):
        self.sensor_id = sensor_id

    def propertyChange(self, event):
        if event.propertyName != "KnownState":
            return
        if event.newValue == jmri.Sensor.ACTIVE:
            state = "OCCUPIED"
        elif event.newValue == jmri.Sensor.INACTIVE:
            state = "UNOCCUPIED"
        else:
            state = "UNKNOWN"

        # Cancel any in-flight debounce timer for this sensor
        existing = _sensor_debounce_timers.get(self.sensor_id)
        if existing is not None:
            existing.stop()

        # Start a fresh timer; only fires if state is still stable after SENSOR_DEBOUNCE_MS
        timer = SwingTimer(SENSOR_DEBOUNCE_MS, SensorDebounceAction(self.sensor_id, state))
        timer.setRepeats(False)
        timer.start()
        _sensor_debounce_timers[self.sensor_id] = timer

for sid, s in sensor_objects.items():
    listener = SensorChangeListener(sid)
    s.addPropertyChangeListener(listener)
    _listeners.append(listener)

# CSV logging layer
CSV_HEADERS = ["timestamp"] + TURNOUT_IDS + SENSOR_IDS
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "eventTrigger_states.csv")

def ensure_csv_file():
    if os.path.exists(CSV_OUTPUT_PATH) and os.path.getsize(CSV_OUTPUT_PATH) > 0:
        return

    with open(CSV_OUTPUT_PATH, "w") as csv_file:
        writer = csv.writer(csv_file, lineterminator="\n")
        writer.writerow(CSV_HEADERS)

def turnout_state_to_text(turnout):
    state = turnout.getCommandedState()
    return "THROWN" if state == jmri.Turnout.THROWN else "CLOSED"

def sensor_state_to_text(sensor):
    state = sensor.getKnownState()
    if state == jmri.Sensor.ACTIVE:
        return "OCCUPIED"
    if state == jmri.Sensor.INACTIVE:
        return "UNOCCUPIED"
    return "UNKNOWN"

def append_state_to_csv():
    ensure_csv_file()
    row = {"timestamp": get_timestamp()}

    for tid, turnout in turnout_objects.items():
        row[tid] = turnout_state_to_text(turnout)

    for sid, sensor in sensor_objects.items():
        row[sid] = sensor_state_to_text(sensor)

    with open(CSV_OUTPUT_PATH, "a") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS, lineterminator="\n")
        writer.writerow(row)

_original_broadcast_state = broadcast_state

def broadcast_state(reason="periodic"):
    append_state_to_csv()
    _original_broadcast_state(reason)

# Initial state dump and broadcast
broadcast_state(reason="startup")

print("")
print("=" * 60)
print("[{}] eventTrigger.py initialized".format(get_timestamp()))
print("  Tracking {} turnouts, {} sensors".format(len(TURNOUT_IDS), len(SENSOR_IDS)))
print("  Broadcasting to {}:{}".format(UDP_IP, UDP_PORT))
print("")
print("  TURNOUT STATES:")
for tid, t in turnout_objects.items():
    state = "THROWN" if t.getCommandedState() == jmri.Turnout.THROWN else "CLOSED"
    print("    {} = {}".format(tid, state))
print("")
print("  SENSOR STATES:")
for sid, s in sensor_objects.items():
    state = s.getKnownState()
    if state == jmri.Sensor.ACTIVE:
        print("    {} = OCCUPIED".format(sid))
    elif state == jmri.Sensor.INACTIVE:
        print("    {} = UNOCCUPIED".format(sid))
    else:
        print("    {} = UNKNOWN".format(sid))
print("=" * 60)
print("")
print("Listening for changes...")
