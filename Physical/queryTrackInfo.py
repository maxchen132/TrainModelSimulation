import json
import socket
from javax.swing import Timer
import jmri

# network config, change directory to json of config
with open("/home/nathanyao/files/cs/purdue/research/MISC/network_config.json") as f:
    config = json.load(f)

UDP_IP = config["broadcast_ip"]
UDP_PORT = config["port"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# init turnouts
turnout1 = turnouts.provideTurnout("DT100")
turnout2 = turnouts.provideTurnout("DT200")

# init signals
btl_red = turnouts.provideTurnout("DT300")
btl_yellow = turnouts.provideTurnout("DT301")
btl_green = turnouts.provideTurnout("DT302")
bsl_red = turnouts.provideTurnout("DT400")
bsl_yellow = turnouts.provideTurnout("DT401")
bsl_green = turnouts.provideTurnout("DT402")

# print("working")

# init blocks
bm = jmri.InstanceManager.getDefault(jmri.BlockManager)

block1 = bm.provideBlock("BLOCK1")
block2 = bm.provideBlock("BLOCK2")
block3 = bm.provideBlock("BLOCK3")

# init trains
tm = jmri.InstanceManager.getDefault(jmri.jmrit.operations.trains.TrainManager)

train1 = tm.newTrain("T1")
train2 = tm.newTrain("T2")

block1.setValue(train1)
block3.setValue(train2)

def broadcast_event(event):
    data = {
        "turnouts": {
            "DT100": turnout1.getCommandedState(),
            "DT200": turnout2.getCommandedState()
        },
        "signals": {
            "BTL_RED": btl_red.getCommandedState(),
            "BTL_YELLOW": btl_yellow.getCommandedState(),
            "BTL_GREEN": btl_green.getCommandedState(),
            "BSL_RED": bsl_red.getCommandedState(),
            "BSL_YELLOW": bsl_yellow.getCommandedState(),
            "BSL_GREEN": bsl_green.getCommandedState()
        },
        "blocks": {}
    }
    
    # iter through all blocks and occupied train
    for block in bm.getNamedBeanSet():
        train = block.getValue()
        data["blocks"][block.getSystemName()] = train.getName() if train else None

    # broadcast
    json_data = json.dumps(data)
    sock.sendto(json_data.encode(), (UDP_IP, UDP_PORT))
    print("Broadcasted:", json_data)

# broadcast every second
timer = Timer(1000, broadcast_event)
timer.start()
