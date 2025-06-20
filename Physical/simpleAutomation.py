import jmri
import jarray

class SimpleAutomation(jmri.jmrit.automat.AbstractAutomaton) :
    def init(self):
        # init() is called exactly once at the beginning to do
        # any necessary configuration.
        print("Inside init(self)")

        # get loco address. For long address change "False" to "True"
        self.throttle_111 = self.getThrottle(111, False)  # short address 111
        self.throttle_2586 = self.getThrottle(2586, True)  # long address 2586

        # get sensor objects
        self.throughStationSensor =  sensors.provideSensor("DS825")
        self.sidingStationSensor =  sensors.provideSensor("DS821")
        self.throughSlowSensor = sensors.provideSensor("DS832")
        self.sidingSlowSensor = sensors.provideSensor("DS835")

        # get turnout objects
        self.right_turnout = turnouts.provideTurnout("DT100")  
        self.left_turnout = turnouts.provideTurnout("DT200")
        # lights
        self.siding_red_light = turnouts.provideTurnout("DT300")
        self.siding_yellow_light = turnouts.provideTurnout("DT301")
        self.siding_green_light = turnouts.provideTurnout("DT302")
        self.through_red_light = turnouts.provideTurnout("DT400")
        self.through_yellow_light = turnouts.provideTurnout("DT401")
        self.through_green_light = turnouts.provideTurnout("DT402")


        return  

    # Assumes that both trains are at their respective stations at script start
    def handle(self):

        # Stop 2586
        self.waitSensorActive(self.sidingStationSensor)
        self.throttle_2586.setSpeedSetting(0.0)
        self.siding_red_light.setCommandedState(THROWN)
        self.siding_green_light.setCommandedState(CLOSED)

        # Set turnouts to closed
        self.right_turnout.setCommandedState(CLOSED)
        self.left_turnout.setCommandedState(CLOSED)

        # Start 111
        self.throttle_111.setIsForward(True)
        self.throttle_111.setSpeedSetting(0.5)
        self.through_red_light.setCommandedState(CLOSED)
        self.through_yellow_light.setCommandedState(CLOSED)
        self.through_green_light.setCommandedState(THROWN)

        self.waitMsec(1000)

        # Slow 111
        self.waitSensorActive(self.throughSlowSensor)
        self.throttle_111.setSpeedSetting(0.2)
        self.through_green_light.setCommandedState(CLOSED)
        self.through_yellow_light.setCommandedState(THROWN)
        
        # Stop 111
        self.waitSensorActive(self.throughStationSensor)
        self.throttle_111.setSpeedSetting(0)
        self.through_red_light.setCommandedState(THROWN)
        self.through_yellow_light.setCommandedState(CLOSED)
        self.through_green_light.setCommandedState(CLOSED)

        # Set turnouts thrown
        self.right_turnout.setCommandedState(THROWN)
        self.left_turnout.setCommandedState(THROWN)

        # Start 2586
        self.throttle_2586.setIsForward(True)
        self.throttle_2586.setSpeedSetting(0.5)
        self.siding_red_light.setCommandedState(CLOSED)
        self.siding_yellow_light.setCommandedState(CLOSED)
        self.siding_green_light.setCommandedState(THROWN)

        self.waitMsec(1000)

        # Slow 2586
        self.waitSensorActive(self.sidingSlowSensor)
        self.throttle_2586.setSpeedSetting(0.2)
        self.siding_green_light.setCommandedState(CLOSED)
        self.siding_yellow_light.setCommandedState(CLOSED)
        self.siding_yellow_light.setCommandedState(THROWN)

        return 1

# end of class definition

SimpleAutomation().start()
