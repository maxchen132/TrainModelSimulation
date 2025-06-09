import jmri
import jarray
from javax.swing import SwingUtilities

class TrainScheduling(jmri.jmrit.automat.AbstractAutomaton) :
    def init(self):
        # init() is called exactly once at the beginning to do
        # any necessary configuration.
        print("Inside init(self)")

        self.DF = jmri.InstanceManager.getDefault(jmri.jmrit.dispatcher.DispatcherFrame)

        if self.DF is None:
            raise Exception("Cannot find any open Dispatcher window.  Start Dispatcher first.")

        self.activeList = self.DF.getActiveTrainsList()

        return  

    def handle(self):
        # handle() is called repeatedly until it returns false.
        #print("Inside handle(self)")

        # access with index

        # train 111
        active_111 = self.activeList.get(0)
        
        active_111.setAutoRun(True)

        # train 2586
        active_2586 = self.activeList.get(1)

        active_2586.setAutoRun(True)

        # and continue around again
        #print("End of Loop")
        return 1
        # (requires JMRI to be terminated to stop - caution
        # doing so could leave loco running if not careful)

# end of class definition

TrainScheduling().start()
