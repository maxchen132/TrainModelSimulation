import json
import socket
from javax.swing import Timer
import jmri
from datetime import datetime


# network config, change directory to json of config
with open("C:\Users\mchen\Documents\Repositories\TrainModelSimulation\Physical\\network_config.json") as f:
    config = json.load(f)

UDP_IP = config["broadcast_ip"]
UDP_PORT = config["port"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

# init turnouts
turnout1 = turnouts.provideTurnout("DT100")
turnout2 = turnouts.provideTurnout("DT200")
turnout1.setUserName("BTL")
turnout2.setUserName("BTR")
turnout1.setCommandedState(jmri.Turnout.CLOSED)
turnout2.setCommandedState(jmri.Turnout.CLOSED)

# init signals
btl_red = turnouts.provideTurnout("DT300")
btl_yellow = turnouts.provideTurnout("DT301")
btl_green = turnouts.provideTurnout("DT302")
bsl_red = turnouts.provideTurnout("DT400")
bsl_yellow = turnouts.provideTurnout("DT401")
bsl_green = turnouts.provideTurnout("DT402")
btl_red.setUserName("BTL_RED")
btl_yellow.setUserName("BTL_YELLOW")    
btl_green.setUserName("BTL_GREEN")
bsl_red.setUserName("BSL_RED")
bsl_yellow.setUserName("BSL_YELLOW")
bsl_green.setUserName("BSL_GREEN")
btl_red.setCommandedState(jmri.Turnout.CLOSED)
btl_yellow.setCommandedState(jmri.Turnout.CLOSED)
btl_green.setCommandedState(jmri.Turnout.CLOSED)
bsl_red.setCommandedState(jmri.Turnout.CLOSED)
bsl_yellow.setCommandedState(jmri.Turnout.CLOSED)
bsl_green.setCommandedState(jmri.Turnout.CLOSED)


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
        "reason": "test",
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
# timer = Timer(1000, broadcast_event)
# timer.start()

def on_turnout_change(event):
    if event.propertyName == "CommandedState":
        state = "THROWN" if event.newValue == jmri.Turnout.THROWN else "CLOSED"
        print("[{}] EVENT - TURNOUT: {} changed to {}".format(get_timestamp(), event.source.getUserName(), state))

turnout1.addPropertyChangeListener(on_turnout_change)
turnout2.addPropertyChangeListener(on_turnout_change)

# Manually defined signal mast groups for now
signal_groups = {
    "SIGNAL_BTL": [btl_red, btl_yellow, btl_green],
    "SIGNAL_BSL": [bsl_red, bsl_yellow, bsl_green]
}

# Since signals are treated as turnouts, multiple signals from the same signal group
# can be on at the same time, so for now it just appends all the currently active lights
# or OFF if theres none
def get_signal_state(heads):
    colors_on = []
    for head in heads:
        state = head.getCommandedState()
        user_name = head.getUserName()
        if state == jmri.Turnout.THROWN:  # 4 = THROWN = ON
            if "RED" in user_name:
                colors_on.append("RED")
            elif "YELLOW" in user_name:
                colors_on.append("YELLOW")
            elif "GREEN" in user_name:
                colors_on.append("GREEN")
    return " ".join(colors_on) if colors_on else "OFF"

def make_signal_listener(group_name, heads):
    def listener(event):
        if event.propertyName == "CommandedState":
            state_str = get_signal_state(heads)
            print("[{}] EVENT - SIGNAL: {} is {}".format(get_timestamp(), group_name, state_str))
    return listener

# attach listener to ALL heads in each group
for name, heads in signal_groups.items():
    listener = make_signal_listener(name, heads)
    for head in heads:
        head.addPropertyChangeListener(listener)

# listeners for blocks
def make_block_listener(block):
    def listener(event):
        
        # print out value of block, train data field doesn't exist
        if event.propertyName == "value":
            block_name = block.getUserName()
            old_train = event.oldValue
            new_train = event.newValue

            print("[{}] EVENT - BLOCK: {} {} EXITED, {} ENTERED".format(
                get_timestamp(), block_name, old_train, new_train))

    return listener

block1.addPropertyChangeListener(make_block_listener(block1))
block2.addPropertyChangeListener(make_block_listener(block2))
block3.addPropertyChangeListener(make_block_listener(block3))
