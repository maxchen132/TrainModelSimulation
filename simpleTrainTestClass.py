import jmri
import jarray

class TrainTest(jmri.jmrit.automat.AbstractAutomaton) :
    def init(self):
        # init() is called exactly once at the beginning to do
        # any necessary configuration.
        print("Inside init(self)")

        # get loco address. For long address change "False" to "True"
        #self.throttle = self.getThrottle(111, False)  # short address 111
        self.throttle = self.getThrottle(2586, True)  # long address 2586

        return  

    def handle(self):
        # handle() is called repeatedly until it returns false.
        print("Inside handle(self)")

        # set loco to forward
        print("Set Loco Forward")
        self.throttle.setIsForward(True)

        # wait 1 second for layout to catch up, then set speed
        self.waitMsec(1000)
        print("Set Speed")
        self.throttle.setSpeedSetting(0.5)
        
        print("wait 5 seconds")
        self.waitMsec(5000)          # wait for 5 seconds
        print("Set Speed Stop")
        self.throttle.setSpeedSetting(0)

        self.waitMsec(5000)           # wait for 5 seconds

        print("Set Loco Reverse")
        self.throttle.setIsForward(False)
        self.waitMsec(1000)                 # wait 1 second for Xpressnet to catch up
        print("Set Speed")
        self.throttle.setSpeedSetting(0.5)

        print("wait 5 seconds")
        self.waitMsec(5000)          # wait for 5 seconds
        print("Set Speed Stop")
        self.throttle.setSpeedSetting(0)

        self.waitMsec(5000)           # wait for 5 seconds

        # and continue around again
        print("End of Loop")
        return 1
        # (requires JMRI to be terminated to stop - caution
        # doing so could leave loco running if not careful)

# end of class definition

TrainTest().start()
