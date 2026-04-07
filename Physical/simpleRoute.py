import jmri

# TURNOUT LOGIC REFERENCE:
# G -> A -> C : DT560 closed, DT500 thrown, DT510 thrown
# G -> A -> D : DT560 closed, DT500 thrown, DT510 closed
# G -> A -> E : DT560 closed, DT500 closed, DT520 closed
# F -> A -> C : DT500 closed, DT510 thrown
# F -> A -> D : DT500 closed, DT510 closed
# F -> A -> E : DT500 thrown, DT520 closed
# E -> G      : DT540 closed
# G -> B      : DT560 thrown
# B -> E      : DT520 thrown
# A -> C      : DT570 thrown
# A -> D      : DT570 closed
# E -> K      : DT540 thrown
# K -> E      : DT540 thrown

# ============================================================
# COMMENT OUT THE NEXT LINE TO DISABLE ALL PRINTING
ENABLE_DEBUG = True
# ============================================================

def log(msg):
    if ENABLE_DEBUG:
        print(msg)

class AutoRoute(jmri.jmrit.automat.AbstractAutomaton):
    def init(self):
        jmri.InstanceManager.getDefault(jmri.PowerManager).setPower(jmri.PowerManager.ON)
        log("Track power ON")
        self.waitMsec(1000)

        log("Getting throttle for loco 2586...")
        self.throttle = self.getThrottle(2586, True)
        log("Got throttle!")

    def set_turnout(self, tid, state):
        t = turnouts.provideTurnout(tid)
        state_str = "THROWN" if state == THROWN else "CLOSED"
        if t.getCommandedState() == state:
            log("  Turnout {} already {}".format(tid, state_str))
            return
        self.waitMsec(100)
        t.setCommandedState(state)
        self.waitMsec(200)
        log("  Turnout {} set to {}".format(tid, state_str))

    def wait_for_sensor(self, sid, name):
        s = sensors.provideSensor(sid)
        log("  Waiting for {} ({})...".format(name, sid))
        while s.getKnownState() != ACTIVE:
            self.waitMsec(100)
        log("  {} ({}) OCCUPIED".format(name, sid))

    def stop_train(self):
        self.throttle.setSpeedSetting(0.0)
        self.waitMsec(300)
        self.throttle.setSpeedSetting(0.0)
        self.waitMsec(300)
        self.throttle.setSpeedSetting(-1)
        self.waitMsec(500)
        self.throttle.setSpeedSetting(0.0)
        self.waitMsec(300)
        self.throttle.setSpeedSetting(-1)
        self.waitMsec(500)

    def handle(self):
        SPEED = 0.5

        # =============================================
        # INITIAL SETUP — train starts at J (IS9)
        # J -> K requires DT550 thrown
        # K -> E requires DT540 thrown
        # =============================================
        log("=== Setting up initial turnout positions ===")
        self.set_turnout("DT550", THROWN)
        self.set_turnout("DT540", THROWN)

        # =============================================
        # PHASE 1: REVERSE  J -> K -> E
        # =============================================
        log("")
        log("=== PHASE 1: REVERSE  J -> K -> E ===")
        self.throttle.setIsForward(False)
        self.throttle.setSpeedSetting(SPEED)

        self.wait_for_sensor("IS12", "K")
        self.wait_for_sensor("IS2", "E")

        # =============================================
        # PHASE 2: STOP at E, switch to FORWARD
        # E -> G requires DT540 closed
        # =============================================
        log("")
        log("=== PHASE 2: STOP at E, prepare for FORWARD ===")

        self.throttle.setSpeedSetting(0)
        self.waitMsec(1000)

        self.set_turnout("DT540", CLOSED)

        self.throttle.setIsForward(True)
        self.throttle.setSpeedSetting(SPEED)

        # =============================================
        # PHASE 3: FORWARD E -> G
        # G -> A -> D : DT560 closed, DT500 thrown, DT510 closed
        # =============================================
        log("")
        log("=== PHASE 3: FORWARD E -> G ===")
        self.set_turnout("DT560", CLOSED)
        self.set_turnout("DT500", THROWN)
        self.set_turnout("DT510", CLOSED)
        self.wait_for_sensor("IS5", "G")

        # =============================================
        # PHASE 4: FORWARD G -> A
        # A -> D : DT570 closed
        # =============================================
        log("")
        log("=== PHASE 4: FORWARD G -> A ===")
        self.set_turnout("DT570", CLOSED)
        self.wait_for_sensor("IS1", "A")

        # =============================================
        # PHASE 5: FORWARD A -> D
        # =============================================
        log("")
        log("=== PHASE 5: FORWARD A -> D ===")
        self.wait_for_sensor("IS6", "D")

        # =============================================
        # PHASE 6: FORWARD D -> F
        # F -> A -> E : DT500 thrown, DT520 closed
        # =============================================
        log("")
        log("=== PHASE 6: FORWARD D -> F ===")
        self.set_turnout("DT500", THROWN)
        self.set_turnout("DT520", CLOSED)
        self.wait_for_sensor("IS8", "F")

        # =============================================
        # PHASE 7: FORWARD F -> A
        # =============================================
        log("")
        log("=== PHASE 7: FORWARD F -> A ===")
        self.wait_for_sensor("IS1", "A")

        # =============================================
        # PHASE 8: FORWARD A -> E
        # E -> G : DT540 closed
        # =============================================
        log("")
        log("=== PHASE 8: FORWARD A -> E ===")
        self.set_turnout("DT540", CLOSED)
        self.wait_for_sensor("IS2", "E")

        # =============================================
        # PHASE 9: FORWARD E -> G
        # G -> B : DT560 thrown
        # =============================================
        log("")
        log("=== PHASE 9: FORWARD E -> G ===")
        self.set_turnout("DT560", THROWN)
        self.wait_for_sensor("IS5", "G")

        # =============================================
        # PHASE 10: FORWARD G -> B — WAIT 10 SECONDS
        # =============================================
        log("")
        log("=== PHASE 10: FORWARD G -> B ===")
        self.wait_for_sensor("IS3", "B")

        log("")
        log("=== ARRIVED AT B — STOPPING FOR 10 SECONDS ===")
        self.stop_train()
        self.waitMsec(10000)
        log("=== 10 SECOND WAIT COMPLETE ===")

        # Resume forward
        # B -> E : DT520 thrown
        self.set_turnout("DT520", THROWN)
        self.throttle.setSpeedSetting(SPEED)

        # =============================================
        # PHASE 11: FORWARD B -> E
        # E -> G : DT540 closed
        # =============================================
        log("")
        log("=== PHASE 11: FORWARD B -> E ===")
        self.set_turnout("DT540", CLOSED)
        self.wait_for_sensor("IS2", "E")

        # =============================================
        # PHASE 12: FORWARD E -> G
        # G -> A -> D : DT560 closed, DT500 thrown, DT510 closed
        # =============================================
        log("")
        log("=== PHASE 12: FORWARD E -> G ===")
        self.set_turnout("DT560", CLOSED)
        self.set_turnout("DT500", THROWN)
        self.set_turnout("DT510", CLOSED)
        self.wait_for_sensor("IS5", "G")

        # =============================================
        # PHASE 13: FORWARD G -> A
        # A -> D : DT570 closed
        # =============================================
        log("")
        log("=== PHASE 13: FORWARD G -> A ===")
        self.set_turnout("DT570", CLOSED)
        self.wait_for_sensor("IS1", "A")

        # =============================================
        # PHASE 14: FORWARD A -> D
        # =============================================
        log("")
        log("=== PHASE 14: FORWARD A -> D ===")
        self.wait_for_sensor("IS6", "D")

        # =============================================
        # PHASE 15: FORWARD D -> F
        # F -> A -> C : DT500 closed, DT510 thrown
        # =============================================
        log("")
        log("=== PHASE 15: FORWARD D -> F ===")
        self.set_turnout("DT500", CLOSED)
        self.set_turnout("DT510", THROWN)
        self.wait_for_sensor("IS8", "F")

        # =============================================
        # PHASE 16: FORWARD F -> A
        # =============================================
        log("")
        log("=== PHASE 16: FORWARD F -> A ===")
        self.wait_for_sensor("IS1", "A")

        # =============================================
        # PHASE 17: FORWARD A -> C
        # A -> C : DT570 thrown (set AFTER reaching A)
        # =============================================
        log("")
        log("=== PHASE 17: FORWARD A -> C ===")
        self.set_turnout("DT570", THROWN)
        self.wait_for_sensor("IS7", "C")

        # =============================================
        # PHASE 18: FORWARD C -> F
        # F -> A -> D : DT500 closed, DT510 closed
        # =============================================
        log("")
        log("=== PHASE 18: FORWARD C -> F ===")
        self.set_turnout("DT500", CLOSED)
        self.set_turnout("DT510", CLOSED)
        self.wait_for_sensor("IS8", "F")

        # =============================================
        # PHASE 19: FORWARD F -> A
        # =============================================
        log("")
        log("=== PHASE 19: FORWARD F -> A ===")
        self.wait_for_sensor("IS1", "A")

        # =============================================
        # PHASE 20: FORWARD A -> D
        # A -> D : DT570 closed (set AFTER reaching A)
        # =============================================
        log("")
        log("=== PHASE 20: FORWARD A -> D ===")
        self.set_turnout("DT570", CLOSED)
        self.wait_for_sensor("IS6", "D")

        # =============================================
        # PHASE 21: FORWARD D -> F
        # F -> A -> E : DT500 thrown, DT520 closed
        # =============================================
        log("")
        log("=== PHASE 21: FORWARD D -> F ===")
        self.set_turnout("DT500", THROWN)
        self.set_turnout("DT520", CLOSED)
        self.wait_for_sensor("IS8", "F")

        # =============================================
        # PHASE 22: FORWARD F -> A
        # =============================================
        log("")
        log("=== PHASE 22: FORWARD F -> A ===")
        self.wait_for_sensor("IS1", "A")

        # =============================================
        # PHASE 23: FORWARD A -> E
        # E -> G : DT540 closed
        # =============================================
        log("")
        log("=== PHASE 23: FORWARD A -> E ===")
        self.set_turnout("DT540", CLOSED)
        self.wait_for_sensor("IS2", "E")

        # =============================================
        # PHASE 24: FORWARD E -> G
        # G -> A -> E : DT560 closed, DT500 closed, DT520 closed
        # =============================================
        log("")
        log("=== PHASE 24: FORWARD E -> G ===")
        self.set_turnout("DT560", CLOSED)
        self.set_turnout("DT500", CLOSED)
        self.set_turnout("DT520", CLOSED)
        self.wait_for_sensor("IS5", "G")

        # =============================================
        # PHASE 25: FORWARD G -> A (loop 1)
        # =============================================
        log("")
        log("=== PHASE 25: FORWARD G -> A ===")
        self.wait_for_sensor("IS1", "A")

        # =============================================
        # PHASE 26: FORWARD A -> E (loop 1)
        # E -> G : DT540 closed
        # =============================================
        log("")
        log("=== PHASE 26: FORWARD A -> E ===")
        self.set_turnout("DT540", CLOSED)
        self.wait_for_sensor("IS2", "E")

        # =============================================
        # PHASE 27: FORWARD E -> G (loop 1)
        # G -> A -> E : DT560 closed, DT500 closed, DT520 closed
        # =============================================
        log("")
        log("=== PHASE 27: FORWARD E -> G ===")
        self.set_turnout("DT560", CLOSED)
        self.set_turnout("DT500", CLOSED)
        self.set_turnout("DT520", CLOSED)
        self.wait_for_sensor("IS5", "G")

        # =============================================
        # PHASE 28: FORWARD G -> A (loop 2)
        # =============================================
        log("")
        log("=== PHASE 28: FORWARD G -> A ===")
        self.wait_for_sensor("IS1", "A")

        # =============================================
        # PHASE 29: FORWARD A -> E (loop 2)
        # E -> G : DT540 closed
        # =============================================
        log("")
        log("=== PHASE 29: FORWARD A -> E ===")
        self.set_turnout("DT540", CLOSED)
        self.wait_for_sensor("IS2", "E")

        # =============================================
        # PHASE 30: FORWARD E -> G (loop 2)
        # G -> A -> E : DT560 closed, DT500 closed, DT520 closed
        # =============================================
        log("")
        log("=== PHASE 30: FORWARD E -> G ===")
        self.set_turnout("DT560", CLOSED)
        self.set_turnout("DT500", CLOSED)
        self.set_turnout("DT520", CLOSED)
        self.wait_for_sensor("IS5", "G")

        # =============================================
        # PHASE 31: FORWARD G -> A (loop 3)
        # =============================================
        log("")
        log("=== PHASE 31: FORWARD G -> A ===")
        self.wait_for_sensor("IS1", "A")

        # =============================================
        # PHASE 32: FORWARD A -> E (loop 3)
        # E -> G : DT540 closed
        # =============================================
        log("")
        log("=== PHASE 32: FORWARD A -> E ===")
        self.set_turnout("DT540", CLOSED)
        self.wait_for_sensor("IS2", "E")

        # =============================================
        # PHASE 33: FORWARD E -> G (loop 3)
        # G -> A -> E : DT560 closed, DT500 closed, DT520 closed
        # =============================================
        log("")
        log("=== PHASE 33: FORWARD E -> G ===")
        self.set_turnout("DT560", CLOSED)
        self.set_turnout("DT500", CLOSED)
        self.set_turnout("DT520", CLOSED)
        self.wait_for_sensor("IS5", "G")

        # =============================================
        # PHASE 34: FORWARD G -> A (loop 4)
        # =============================================
        log("")
        log("=== PHASE 34: FORWARD G -> A ===")
        self.wait_for_sensor("IS1", "A")

        # =============================================
        # PHASE 35: FORWARD A -> E (final, heading to yard)
        # E -> K : DT540 thrown
        # =============================================
        log("")
        log("=== PHASE 35: FORWARD A -> E ===")
        self.set_turnout("DT540", THROWN)
        self.wait_for_sensor("IS2", "E")

        # =============================================
        # PHASE 36: FORWARD E -> K
        # K -> J : DT550 thrown (should already be)
        # =============================================
        log("")
        log("=== PHASE 36: FORWARD E -> K ===")
        self.set_turnout("DT550", THROWN)
        self.wait_for_sensor("IS12", "K")

        # =============================================
        # PHASE 37: FORWARD K -> J — HOME
        # Slow down for approach into yard
        # =============================================
        log("")
        log("=== PHASE 37: FORWARD K -> J ===")
        self.throttle.setSpeedSetting(0.25)
        self.wait_for_sensor("IS9", "J")

        # Let train roll fully into the block
        self.waitMsec(1000)

        # =============================================
        # ARRIVED AT J — STOP
        # =============================================
        log("")
        log("=== ARRIVED AT J — STOPPING ===")
        self.throttle.setSpeedSetting(0.0)
        self.waitMsec(200)
        self.stop_train()
        self.waitMsec(500)
        self.stop_train()
        self.throttle.release()
        log("=== ROUTE COMPLETE ===")

        return False

AutoRoute("autoroute").start()
