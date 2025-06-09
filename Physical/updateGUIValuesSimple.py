import jmri
import jarray

class UpdateGUI(jmri.jmrit.automat.AbstractAutomaton) :
    def init(self):
        # init() is called exactly once at the beginning to do
        # any necessary configuration.
        print("Inside init(self)")

        self.memoryManager = jmri.InstanceManager.getDefault(jmri.MemoryManager)
        self.trainSpeed = self.memoryManager.getMemory("IMTRAINSPEED")       # using System Name
        self.throttle1 = self.getThrottle(2586, True)

        self.lightManager = jmri.InstanceManager.getDefault(jmri.LightManager)
        self.clockwiseLight = self.lightManager.getLight("DL100")
        self.PTCEngagedLight = self.lightManager.getLight("DL200")
        self.autoOpLight = self.lightManager.getLight("DL300")
        self.PTCOverrideLight = self.lightManager.getLight("DL400")

        return  

    def handle(self):
        # handle() is called repeatedly until it returns false.
        #print("Inside handle(self)")

        currentSpeed = self.throttle1.getSpeedSetting()

        self.trainSpeed.setValue(currentSpeed)

        if self.clockwiseLight.getState() == 4:
            self.clockwiseLight.setState(2)
        else:
            self.clockwiseLight.setState(4)

        self.waitMsec(100)
        #print(self.trainSpeed.getValue())  
        # and continue around again
        #print("End of Loop")
        return 1
        # (requires JMRI to be terminated to stop - caution
        # doing so could leave loco running if not careful)

# end of class definition

UpdateGUI().start()