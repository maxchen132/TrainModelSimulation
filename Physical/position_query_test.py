

left_turnout = turnouts.provideTurnout("DT200")
print(left_turnout.commandedState == CLOSED)
signal1_red = turnouts.provideTurnout("DT526")
print(signal1_red.commandedState == CLOSED)

# This is an example script for a JMRI "Automat" in Python
#
# It listens to two sensors, running a locomotive back and
# forth between them by changing its direction when a sensor
# detects the engine. You need to set the speed of the engine
# using a throttle.
#
# Author: Bob Jacobsen, copyright 2004, 2005
# Part of the JMRI distribution

import jarray
import jmri


class AutomatExample(jmri.jmrit.automat.AbstractAutomaton) :
   
    # init() is called exactly once at the beginning to do
    # any necessary configuration.
    def init(self):
       
        # get the sensor and throttle objects
        self.sensors = sensors.provideSensor("IS100")
        self.sensor2 = sensors.provideSensor("IS100")
        self.sensor3 = sensors.provideSensor("IS100")
               
        return


    # handle() is called repeatedly until it returns false.
    #
    # Modify this to do your calculation.
    def handle(self):

        # wait for sensor in forward direction to trigger
        self.waitSensorActive(self.sensor1)
       
        print("sensor active")
        print("Occupied blocks:")
        print(self.findOccupiedBlocks())

        # wait for sensor inactive, meaning loco has reversed out
        # (prevent infinite loop if both sensors go active in the overlap)
        self.waitSensorInactive(self.sensor1)
        print("sensor inactive")
       
        # and continue around again
        return 1    # to continue

    def findCurrentBlocks(self):
	# search the block list for the matching loco
        blockList = []
        for b in blocks.getNamedBeanSet() :
            blockList.append(b)
	    
        return blockList
    
    def findOccupiedBlocks(self):
	    blockNamesList = []
        for b in blocks.getNamedBeanSet() :
            if (b.getState() == ACTIVE) :
                blockNamesList.append(b)
	
        return blockList

   
# end of class definition

# create one of these
a = AutomatExample()

# set the name, as a example of configuring it
a.setName("Automat example script")

# and start it running
a.start()

