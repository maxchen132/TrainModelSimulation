import jmri
from java.util.concurrent.locks import ReentrantLock

# ============================================================
# CONFIG
# ============================================================
DEBUG = True
DEFAULT_SPEED = 0.50
APPROACH_SPEED = 0.25

# JMRI block -> occupancy sensor map from your XML
BLOCK_SENSOR = {
    "A": "IS1",   # A_Crossover / S_Crossover
    "B": "IS3",   # B_Inner_Siding / S_Inner_Siding
    "C": "IS7",   # C_Outer_Scenic
    "D": "IS6",   # D_Outer_East
    "E": "IS2",   # E_Inner_East / S_Inner_East
    "F": "IS8",   # F_Outer_West
    "G": "IS5",   # G_Inner_West
    "H": "IS11",  # H_Yard_3
    "I": "IS10",  # I_Yard_2
    "J": "IS9",   # J_Yard_1
    "K": "IS12",  # K_Yard_Lead
}

# A small reservation system so two automatons never command the same block
class BlockArbiter(object):
    def __init__(self):
        self._map_lock = ReentrantLock()
        self._locks = {}

    def _lock_for(self, block_name):
        self._map_lock.lock()
        try:
            lock = self._locks.get(block_name)
            if lock is None:
                lock = ReentrantLock()
                self._locks[block_name] = lock
            return lock
        finally:
            self._map_lock.unlock()

    def reserve(self, block_name, who):
        log("{} reserving block {}".format(who, block_name))
        self._lock_for(block_name).lock()

    def release(self, block_name, who):
        lock = self._lock_for(block_name)
        if lock.isHeldByCurrentThread():
            lock.unlock()
            log("{} released block {}".format(who, block_name))

ARB = BlockArbiter()

def log(msg):
    if DEBUG:
        print(msg)

def sensor_state(sensor_id):
    return sensors.provideSensor(sensor_id).getKnownState()

def block_clear(block_name):
    return sensor_state(BLOCK_SENSOR[block_name]) != ACTIVE

def block_occupied(block_name):
    return sensor_state(BLOCK_SENSOR[block_name]) == ACTIVE


class BaseRoute(jmri.jmrit.automat.AbstractAutomaton):
    loco = None
    name = ""

    def init(self):
        jmri.InstanceManager.getDefault(jmri.PowerManager).setPower(jmri.PowerManager.ON)
        log("[{}] Track power ON".format(self.name))
        self.waitMsec(1000)

        self.throttle = self.getThrottle(self.loco, True)
        log("[{}] Got throttle for loco {}".format(self.name, self.loco))
        return True

    def set_turnout(self, tid, state):
        t = turnouts.provideTurnout(tid)
        if t.getCommandedState() == state:
            return
        t.setCommandedState(state)
        self.waitMsec(150)

    def set_turnouts(self, pairs):
        for tid, state in pairs:
            self.set_turnout(tid, state)

    def wait_for_occupied(self, block_name):
        sid = BLOCK_SENSOR[block_name]
        log("[{}] Waiting for block {} ({}) occupied".format(self.name, block_name, sid))
        while sensor_state(sid) != ACTIVE:
            self.waitMsec(100)
        log("[{}] Block {} occupied".format(self.name, block_name))

    def wait_for_clear(self, block_name):
        sid = BLOCK_SENSOR[block_name]
        log("[{}] Waiting for block {} ({}) clear".format(self.name, block_name, sid))
        while sensor_state(sid) == ACTIVE:
            self.waitMsec(100)
        log("[{}] Block {} clear".format(self.name, block_name))

    def reserve_block(self, block_name):
        ARB.reserve(block_name, self.name)

    def release_block(self, block_name):
        ARB.release(block_name, self.name)

    def stop_and_wait(self, ms):
        self.throttle.setSpeedSetting(0.0)
        self.waitMsec(ms)

    def move_to(self, from_block, to_block, turnouts_to_set=None,
                forward=None, speed=None, dwell_ms=0):
        """
        Reserve destination block first, line turnouts, move, wait for destination
        occupancy, then release the previous block.
        """
        self.wait_for_clear(to_block)
        self.reserve_block(to_block)

        if turnouts_to_set:
            self.set_turnouts(turnouts_to_set)

        if forward is not None:
            self.throttle.setIsForward(forward)
        if speed is not None:
            self.throttle.setSpeedSetting(speed)

        self.wait_for_occupied(to_block)

        if from_block is not None:
            self.release_block(from_block)

        if dwell_ms > 0:
            self.stop_and_wait(dwell_ms)

    def finish(self, current_block):
        self.throttle.setSpeedSetting(0.0)
        self.waitMsec(250)
        if current_block is not None:
            self.release_block(current_block)
        self.throttle.release()
        log("[{}] Route complete".format(self.name))


class Train2586(BaseRoute):
    name = "Train2586"
    loco = 2586

    def handle(self):
        SPEED = DEFAULT_SPEED

        # Start at J
        self.wait_for_occupied("J")
        self.reserve_block("J")

        # Initial turnout setup for J -> K -> E
        self.set_turnouts([
            ("DT550", THROWN),
            ("DT540", THROWN),
        ])

        # J -> K -> E (reverse)
        self.throttle.setIsForward(False)
        self.throttle.setSpeedSetting(SPEED)

        self.move_to("J", "K")
        self.move_to("K", "E")

        # Stop at E, switch direction to forward
        self.stop_and_wait(1000)
        self.set_turnout("DT540", CLOSED)

        self.throttle.setIsForward(True)
        self.throttle.setSpeedSetting(SPEED)

        # E -> G
        self.move_to("E", "G", [
            ("DT560", CLOSED),
            ("DT500", THROWN),
            ("DT510", CLOSED),
        ])

        # G -> A
        self.move_to("G", "A", [
            ("DT570", CLOSED),
        ])

        # A -> D
        self.move_to("A", "D")

        # D -> F
        self.move_to("D", "F", [
            ("DT500", THROWN),
            ("DT520", CLOSED),
        ])

        # F -> A
        self.move_to("F", "A")

        # A -> E
        self.move_to("A", "E", [
            ("DT540", CLOSED),
        ])

        # E -> G
        self.move_to("E", "G", [
            ("DT560", THROWN),
        ])

        # G -> B
        self.move_to("G", "B")

        # Wait 10 seconds at B
        self.stop_and_wait(10000)
        self.throttle.setSpeedSetting(SPEED)

        # B -> E
        self.move_to("B", "E", [
            ("DT520", THROWN),
        ])

        # E -> G
        self.move_to("E", "G", [
            ("DT540", CLOSED),
        ])

        # G -> A
        self.move_to("G", "A", [
            ("DT560", CLOSED),
            ("DT500", THROWN),
            ("DT510", CLOSED),
        ])

        # A -> D
        self.move_to("A", "D", [
            ("DT570", CLOSED),
        ])

        # D -> F
        self.move_to("D", "F", [
            ("DT500", CLOSED),
            ("DT510", THROWN),
        ])

        # F -> A
        self.move_to("F", "A")

        # A -> C
        self.move_to("A", "C", [
            ("DT570", THROWN),
        ])

        # C -> F
        self.move_to("C", "F", [
            ("DT500", CLOSED),
            ("DT510", CLOSED),
        ])

        # F -> A
        self.move_to("F", "A")

        # A -> D
        self.move_to("A", "D", [
            ("DT570", CLOSED),
        ])

        # D -> F
        self.move_to("D", "F", [
            ("DT500", THROWN),
            ("DT520", CLOSED),
        ])

        # F -> A
        self.move_to("F", "A")

        # A -> E
        self.move_to("A", "E", [
            ("DT540", CLOSED),
        ])

        # E -> G
        self.move_to("E", "G", [
            ("DT560", CLOSED),
            ("DT500", CLOSED),
            ("DT520", CLOSED),
        ])

        # A/G loop a few times as in your original script
        self.move_to("G", "A")
        self.move_to("A", "E", [("DT540", CLOSED)])
        self.move_to("E", "G", [
            ("DT560", CLOSED),
            ("DT500", CLOSED),
            ("DT520", CLOSED),
        ])

        self.move_to("G", "A")
        self.move_to("A", "E", [("DT540", CLOSED)])
        self.move_to("E", "G", [
            ("DT560", CLOSED),
            ("DT500", CLOSED),
            ("DT520", CLOSED),
        ])

        self.move_to("G", "A")
        self.move_to("A", "E", [("DT540", CLOSED)])
        self.move_to("E", "G", [
            ("DT560", CLOSED),
            ("DT500", CLOSED),
            ("DT520", CLOSED),
        ])

        self.move_to("G", "A")
        self.move_to("A", "E", [("DT540", THROWN)])

        # E -> K -> J
        self.move_to("E", "K", [
            ("DT550", THROWN),
        ])

        self.throttle.setSpeedSetting(APPROACH_SPEED)
        self.move_to("K", "J")
        self.waitMsec(1000)

        self.finish("J")
        return False


class Train111(BaseRoute):
    name = "Train111"
    loco = 111

    def handle(self):
        SPEED = DEFAULT_SPEED

        # Start at I_Yard_2 / IS10
        self.wait_for_occupied("I")
        self.reserve_block("I")

        # Hold at I for 15 seconds
        self.stop_and_wait(15000)

        # Yard lead lining: adjust if your physical I->K ladder needs a different state
        self.set_turnouts([
            ("TOL126", THROWN),
            ("TOL125", CLOSED),
        ])

        # Reverse and go I -> K -> E
        self.throttle.setIsForward(False)
        self.throttle.setSpeedSetting(SPEED)

        self.move_to("I", "K")
        self.move_to("K", "E", [
            ("DT540", THROWN),
        ])

        # Stop at E, then forward
        self.stop_and_wait(1000)
        self.set_turnout("DT540", CLOSED)

        self.throttle.setIsForward(True)
        self.throttle.setSpeedSetting(SPEED)

        # E -> G
        self.move_to("E", "G", [
            ("DT560", CLOSED),
            ("DT500", THROWN),
            ("DT510", CLOSED),
        ])

        # G -> A -> C -> F -> A -> E -> G -> B
        for cycle in range(3):
            self.move_to("G", "A", [
                ("DT570", THROWN),
            ])
            self.move_to("A", "C")
            self.move_to("C", "F", [
                ("DT500", CLOSED),
                ("DT510", THROWN),
            ])
            self.move_to("F", "A")
            self.move_to("A", "E", [
                ("DT540", CLOSED),
            ])
            self.move_to("E", "G", [
                ("DT560", THROWN if cycle == 0 else CLOSED),
            ])
            self.move_to("G", "B")

            # Wait 10 seconds at B after each loop
            self.stop_and_wait(10000)
            self.throttle.setSpeedSetting(SPEED)

            if cycle < 2:
                self.move_to("B", "E", [
                    ("DT520", THROWN),
                ])
                self.move_to("E", "G", [
                    ("DT540", CLOSED),
                ])

        # Final exit: E -> K -> I
        self.move_to("B", "E", [
            ("DT520", THROWN),
        ])
        self.move_to("E", "K", [
            ("DT540", THROWN),
        ])

        self.throttle.setSpeedSetting(APPROACH_SPEED)
        self.move_to("K", "I")
        self.waitMsec(1000)

        self.finish("I")
        return False


# ============================================================
# START BOTH ROUTES
# ============================================================
Train2586("Train2586").start()
Train111("Train111").start()