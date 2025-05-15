import jmri
import time


# Get a turnout by its system name or user name
turnout = turnouts.provideTurnout("DT100")  

turnout.setCommandedState(THROWN)
time.sleep(1)
turnout.setCommandedState(CLOSED)

