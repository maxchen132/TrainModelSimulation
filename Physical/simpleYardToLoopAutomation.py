import jmri
import jarray

# ============================================================
#  YARD SPUR → INNER LOOP → RETURN AUTOMATION
#  Layout: CERIAS Train v2
#
#  Route overview:
#   1. Engine starts in Yard_1 spur (stopped, facing outward/reverse)
#   2. Back (reverse) out through Yard_Lead → Inner_East
#   3. Proceed clockwise: Inner_East → Inner_West (via inner loop)
#   4. Re-enter yard via Yard_Lead → Yard_1 spur (forward into spur)
#
#  Turnout map (from XML):
#   TOL125 (DT540 physical) - Yard_Lead → Yard_1 branch
#   TOL126 (DT550 physical) - Yard_Lead → Yard_2/Yard_3 branch
#   TOR77  (DT520 physical) - Inner_East ↔ Yard_Lead junction
#   TOR36  (DT510 physical) - Inner_West: Through vs Siding
#   TOL52  (DT500 physical) - Inner_East: Through vs Siding
#
#  Sensor map — ADD THESE to your layout (see notes at bottom):
#   DS1  - Yard_1 spur (already defined in XML)
#   DS2  - Yard_Lead (detect engine in lead track)
#   DS3  - Inner_East slow-down zone (approaching yard junction)
#   DS4  - Inner_West slow-down zone (approaching inner_west)
#   DS5  - Inner_West station/midpoint (confirm loop complete)
# ============================================================

class YardToLoopAutomation(jmri.jmrit.automat.AbstractAutomaton):

    # --- Tuneable constants ---
    LOCO_ADDRESS   = 111       # Change to your loco's DCC address
    LONG_ADDRESS   = False     # True if using a long (4-digit) address
    SPEED_FULL     = 0.4       # Normal running speed (0.0–1.0)
    SPEED_SLOW     = 0.15      # Slow/approach speed
    SETTLE_MS      = 1500      # Wait after turnout throw before moving (ms)
    DEPART_MS      = 2000      # Wait after starting before checking sensors (ms)

    def init(self):
        print("[YardLoop] Initialising automation...")

        # Throttle
        self.throttle = self.getThrottle(self.LOCO_ADDRESS, self.LONG_ADDRESS)
        if self.throttle is None:
            print("[YardLoop] ERROR: Could not acquire throttle for address "
                  + str(self.LOCO_ADDRESS))

        # --- Sensors ---
        # DS1 is pre-configured in the XML (Pin 4, pullup).
        # DS2–DS5 must be wired to your Arduino and added to Panel Pro.
        self.sensor_yard1     = sensors.provideSensor("DS1")  # Yard_1 spur occupied
        self.sensor_yardLead  = sensors.provideSensor("DS2")  # Yard_Lead occupied
        self.sensor_innerEast = sensors.provideSensor("DS3")  # Inner_East slow zone
        self.sensor_innerWest = sensors.provideSensor("DS4")  # Inner_West slow zone
        self.sensor_loopDone  = sensors.provideSensor("DS5")  # Inner_West confirm point

        # --- Turnouts ---
        # DT540 / TOL125 : splits Yard_Lead → Yard_1 (CLOSED) vs Yard_2/3 (THROWN)
        self.to_yard1   = turnouts.provideTurnout("DT540")
        # DT550 / TOL126 : splits Yard_Lead → Yard_3 (CLOSED) vs Yard_2 (THROWN)
        self.to_yard23  = turnouts.provideTurnout("DT550")
        # DT520 / TOR77  : Inner_East ↔ Yard_Lead (CLOSED=inner loop, THROWN=yard)
        self.to_yardJct = turnouts.provideTurnout("DT520")
        # DT510 / TOR36  : Inner_West through (CLOSED) vs siding (THROWN)
        self.to_innerW  = turnouts.provideTurnout("DT510")
        # DT500 / TOL52  : Inner_East through (CLOSED) vs siding (THROWN)
        self.to_innerE  = turnouts.provideTurnout("DT500")

        print("[YardLoop] Init complete.")
        return

    def handle(self):
        print("[YardLoop] Starting sequence...")

        # --------------------------------------------------------
        # PHASE 1: Set turnouts for backing out of Yard_1
        #   TOL125 CLOSED  → route goes to Yard_1 branch
        #   TOL126 THROWN  → not used for Yard_1, keep clear
        #   TOR77  THROWN  → connects Yard_Lead to Inner_East
        #   TOR36  CLOSED  → Inner_West on through track
        #   TOL52  CLOSED  → Inner_East on through track
        # --------------------------------------------------------
        print("[YardLoop] Phase 1: Setting turnouts for departure...")
        self.to_yard1.setCommandedState(CLOSED)
        self.to_yard23.setCommandedState(THROWN)   # keep Yard_2/3 routes clear
        self.to_yardJct.setCommandedState(THROWN)  # TOR77: divert toward yard lead
        self.to_innerW.setCommandedState(CLOSED)   # through inner west
        self.to_innerE.setCommandedState(CLOSED)   # through inner east
        self.waitMsec(self.SETTLE_MS)

        # --------------------------------------------------------
        # PHASE 2: Back engine out of spur into Yard_Lead
        # --------------------------------------------------------
        print("[YardLoop] Phase 2: Reversing out of Yard_1 spur...")
        self.throttle.setIsForward(False)          # reverse = backing out of spur
        self.throttle.setSpeedSetting(self.SPEED_SLOW)
        self.waitMsec(self.DEPART_MS)

        # Wait until engine clears the spur and is in Yard_Lead
        self.waitSensorActive(self.sensor_yardLead)
        print("[YardLoop] Engine detected in Yard_Lead.")

        # Stop briefly, then throw TOR77 to CLOSED so engine can
        # continue backing onto the Inner_East block
        self.throttle.setSpeedSetting(0.0)
        self.waitMsec(500)
        self.to_yardJct.setCommandedState(CLOSED)  # TOR77: now routes to inner loop
        self.waitMsec(self.SETTLE_MS)

        # Continue reversing slowly into Inner_East
        self.throttle.setSpeedSetting(self.SPEED_SLOW)

        # --------------------------------------------------------
        # PHASE 3: Switch direction — now go forward (clockwise)
        # --------------------------------------------------------
        # Wait until the engine is fully in Inner_East
        self.waitSensorActive(self.sensor_innerEast)
        print("[YardLoop] Engine in Inner_East — switching to forward.")
        self.throttle.setSpeedSetting(0.0)
        self.waitMsec(800)

        self.throttle.setIsForward(True)
        self.throttle.setSpeedSetting(self.SPEED_FULL)

        # --------------------------------------------------------
        # PHASE 4: Clockwise inner loop
        #   Inner_East → (through TOL52 CLOSED) →
        #   Inner_Through → Inner_West → (through TOR36 CLOSED) →
        #   Inner_East  (completes one loop)
        # --------------------------------------------------------
        print("[YardLoop] Phase 4: Running clockwise inner loop...")

        # Slow down as engine approaches Inner_West
        self.waitSensorActive(self.sensor_innerWest)
        print("[YardLoop] Approaching Inner_West — slowing.")
        self.throttle.setSpeedSetting(self.SPEED_SLOW)

        # Confirm loop is complete (engine back at Inner_East sensor)
        self.waitSensorActive(self.sensor_loopDone)
        print("[YardLoop] Loop confirmed complete — beginning return to yard.")
        self.throttle.setSpeedSetting(self.SPEED_SLOW)

        # --------------------------------------------------------
        # PHASE 5: Divert back into yard
        #   Set TOR77 THROWN to route from Inner_East into Yard_Lead
        #   Set TOL125 CLOSED to route into Yard_1
        # --------------------------------------------------------
        print("[YardLoop] Phase 5: Setting turnouts for yard re-entry...")
        self.to_yardJct.setCommandedState(THROWN)   # TOR77: route to Yard_Lead
        self.to_yard1.setCommandedState(CLOSED)      # TOL125: route to Yard_1
        self.to_yard23.setCommandedState(THROWN)
        self.waitMsec(self.SETTLE_MS)

        # Wait until engine enters Yard_Lead
        self.waitSensorActive(self.sensor_yardLead)
        print("[YardLoop] Engine in Yard_Lead — slow approach to spur.")
        self.throttle.setSpeedSetting(self.SPEED_SLOW)

        # --------------------------------------------------------
        # PHASE 6: Pull forward into Yard_1 spur and stop
        # --------------------------------------------------------
        self.waitSensorActive(self.sensor_yard1)
        print("[YardLoop] Engine back in Yard_1 — stopping.")
        self.throttle.setSpeedSetting(0.0)

        # Optionally restore turnouts to default state
        self.to_yardJct.setCommandedState(CLOSED)
        self.to_yard1.setCommandedState(CLOSED)

        print("[YardLoop] Sequence complete.")
        return 0   # return 0 to run once; return 1 to loop indefinitely

# end class

YardToLoopAutomation().start()