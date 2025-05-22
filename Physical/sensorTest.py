import jmri
import jarray

class TrainTest(jmri.jmrit.automat.AbstractAutomaton) :
    def init(self):
        # init() is called exact    ly once at the beginning to do
        # any necessary configuration.
        print("Inside init(self)")

        # set up sensor numbers
        # fwdSensor is reached when loco is running forward
        self.firstSensor = sensors.provideSensor("DS35")
        self.secondSensor = sensors.provideSensor("DS36")

        # get loco address. For long address change "False" to "True"
        self.throttle1 = self.getThrottle(111, False)  # short address 111
        self.throttle2 = self.getThrottle(2586, True)  # long address 2586

        return  

    def handle(self):
        # handle() is called repeatedly until it returns false.
        print("Inside handle(self)")

        # set loco to forward
        print("Set Loco Forward")
        self.throttle1.setIsForward(True)

        # wait for sensor to (de)activate before starting
        print("Wait for Forward Sensor")
        self.waitSensorInactive(self.firstSensor)

        print("Set Speed")
        self.throttle1.setSpeedSetting(0.3)
        
        # stop when sensor is activated
        print("Wait for Stop Sensor")
        self.waitSensorActive(self.firstSensor)

        print("Set Speed Stop")
        self.throttle1.setSpeedSetting(0)

        print("Set Loco Reverse")
        self.throttle1.setIsForward(False)

        # wait for sensor to (de)activate before starting
        print("Wait for Backwards Sensor")
        self.waitSensorInactive(self.firstSensor)

        print("Set Speed")
        self.throttle1.setSpeedSetting(0.3)

        # stop when sensor is activated
        print("Wait for Stop Sensor")
        self.waitSensorActive(self.firstSensor)

        print("Set Speed Stop")
        self.throttle1.setSpeedSetting(0)

        # and continue around again
        print("End of Loop")
        return 1
        # (requires JMRI to be terminated to stop - caution
        # doing so could leave loco running if not careful)

# end of class definition

TrainTest().start()
