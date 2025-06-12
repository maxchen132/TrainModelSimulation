import jmri
import jarray

class UpdateGUI(jmri.jmrit.automat.AbstractAutomaton) :
    def init(self):
        # init() is called exactly once at the beginning to do
        # any necessary configuration.
        print("Inside init(self)")

        self.memoryManager = jmri.InstanceManager.getDefault(jmri.MemoryManager)
        self.trainSpeed = self.memoryManager.getMemory("IMTRAINSPEED")       # using System Name
        self.interruptMessage = self.memoryManager.getMemory("IMINTERRUPTMSG")
        self.warningMessage = self.memoryManager.getMemory("IMWARNINGMSG")

        self.throttle1 = self.getThrottle(2586, True)

        self.lightManager = jmri.InstanceManager.getDefault(jmri.LightManager)
        self.clockwiseLight = self.lightManager.getLight("ILDL100")
        self.PTCEngagedLight = self.lightManager.getLight("ILDL200")
        self.autoOpLight = self.lightManager.getLight("ILDL300")
        self.PTCOverrideLight = self.lightManager.getLight("ILDL400")

        self.interruptMessage.setValue("")
        self.warningMessage.setValue("")
        self.PTCOverrideLight.setState(2)  # off
        self.autoOpLight.setState(2)  # off
        self.ptcEngaged = False
        self.clockwise = True
        self.ptcOverriden = False

        return  

    def handle(self):
        # handle() is called repeatedly until it returns false.
        #print("Inside handle(self)")

        # logic for PTC override:
        if self.PTCOverrideLight.getState() == 4:
            self.ptcOverriden = True
            self.ptcEngaged = False
            self.interruptMessage.setValue("")
            self.warningMessage.setValue("")
        else:
            self.ptcOverriden = False

        currentSpeed = round(self.throttle1.getSpeedSetting(), 2)

        # logic for PTC, can be expanded
        if not self.ptcOverriden:
            if currentSpeed > 0.9 or currentSpeed < -0.9: 
                self.throttle1.setSpeedSetting(0)
                self.ptcEngaged = True
                self.PTCEngagedLight.setState(4) # might need to swap to 2
                self.interruptMessage.setValue("PTC Engaged!")
                self.warningMessage.setValue("Speed Limit Exceeded! Emergency Brake!")

        # state == 2 means off, state == 4 means on
        if self.ptcEngaged == True:
            self.throttle1.setSpeedSetting(0)
            if self.PTCEngagedLight.getState() == 2:
                self.ptcEngaged = False
                self.interruptMessage.setValue("")
                self.warningMessage.setValue("")
        else:
            self.PTCEngagedLight.setState(2)

        # updates throttle value to the GUI
        # TODO: translate to MPH, or find more elegant speedometer solution
        self.trainSpeed.setValue(currentSpeed)

        # logic for control and display of train direction status
        if self.clockwise == True:
            if self.clockwiseLight.getState() == 2:
                self.clockwise = False
                self.throttle1.setIsForward(False)
        else:
            if self.clockwiseLight.getState() == 4:
                self.clockwise = True
                self.throttle1.setIsForward(True)
        

        if self.throttle1.getIsForward() == True:
            self.clockwise = True
            self.clockwiseLight.setState(4)
        else:
            self.clockwise = False
            self.clockwiseLight.setState(2)

        # logic for autoOperator display light

        # updates 10 times every second
        self.waitMsec(100)

        # and continue around again
        #print("End of Loop")
        return 1
        # (requires JMRI to be terminated to stop - caution
        # doing so could leave loco running if not careful)

# end of class definition

UpdateGUI().start()
