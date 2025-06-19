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

        # get turnout objects
        self.right_turnout = turnouts.provideTurnout("DT100")  
        self.left_turnout = turnouts.provideTurnout("DT200")
        #lights
        self.siding_red_light = turnouts.provideTurnout("DT300")
        self.siding_yellow_light = turnouts.provideTurnout("DT301")
        self.siding_green_light = turnouts.provideTurnout("DT302")
        self.through_red_light = turnouts.provideTurnout("DT400")
        self.through_yellow_light = turnouts.provideTurnout("DT401")
        self.through_green_light = turnouts.provideTurnout("DT402")


        return  

    def handle(self):

        self.waitSensorActive(self.sidingStationSensor)
        self.throttle_2586.setSpeedSetting(0.0)
        self.siding_red_light.setCommandedState(THROWN)
        self.siding_green_light.setCommandedState(CLOSED)
        #self.waitSensorActive(self.throughStationSensor)

        self.right_turnout.setCommandedState(CLOSED)
        self.left_turnout.setCommandedState(CLOSED)

        self.throttle_111.setIsForward(True)
        self.throttle_111.setSpeedSetting(0.5)
        self.through_red_light.setCommandedState(CLOSED)
        self.through_green_light.setCommandedState(THROWN)

        self.waitMsec(1000)
        
        self.waitSensorActive(self.throughStationSensor)
        self.throttle_111.setSpeedSetting(0)
        self.through_red_light.setCommandedState(THROWN)
        self.through_green_light.setCommandedState(CLOSED)
        #self.waitSensorActive(self.sidingStationSensor)

        self.right_turnout.setCommandedState(THROWN)
        self.left_turnout.setCommandedState(THROWN)

        self.throttle_2586.setIsForward(True)
        self.throttle_2586.setSpeedSetting(0.5)
        self.siding_red_light.setCommandedState(CLOSED)
        self.siding_green_light.setCommandedState(THROWN)

        self.waitMsec(1000)

        return 1

# end of class definition

SimpleAutomation().start()
