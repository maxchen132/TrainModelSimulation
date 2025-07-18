// TURNOUT CONTROL 
// NEED TO FIX, USE PWM PIN TO NOT BURN SOLENOID
#define PULSE 50 // 50ms
#define I2C_ADDRESS 0x65

// DEFINE SINGLE_COIL_TURNOUT MACRO
#define SINGLE_COIL_TURNOUT(t, p1, p2, desc) \
VIRTUAL_TURNOUT(t, desc) \
DONE \
ONCLOSE(t) \
  SET(p1) DELAY (PULSE) RESET(p1) \
DONE \
ONTHROW(t) \
  SET(p2) DELAY(PULSE) RESET(p2) \
DONE

// DEFINE LED AS MACRO
#define LED_TURNOUT(t, p, desc) \
VIRTUAL_TURNOUT(t, desc) \
DONE \
ONCLOSE(t) \
  SET(p) \
DONE \
ONTHROW(t) \
  RESET(p) \
DONE


ROSTER(2586, "NS")
//ROSTER(111, "CSX")

SINGLE_COIL_TURNOUT(100, 23, 22, "Right Turnout")
SINGLE_COIL_TURNOUT(200, 25, 24, "Left Turnout")

LED_TURNOUT(150, 826, "TEST")

//BTL
JMRI_SENSOR(821)
LED_TURNOUT(300, 818, "BTL_RED")
LED_TURNOUT(301, 819, "BTL_YELLOW")
LED_TURNOUT(302, 820, "BTL_GREEN")

//BSL
JMRI_SENSOR(825)
LED_TURNOUT(400, 822, "BSL_RED")
LED_TURNOUT(401, 823, "BSL_YELLOW")
LED_TURNOUT(402, 824, "BSL_GREEN")

/*
// TRAFFIC SIGNAL 
// GREEN: 28, AMBER: 27, RED: 26
SIGNAL(26, 27, 28)

VIRTUAL_SIGNAL(300)
*/

// VPIN for current sensor
JMRI_SENSOR(144)
JMRI_SENSOR(145)
JMRI_SENSOR(146)

//TURN ON PIN 2 OF EXPANDER ARDUINO
SEQUENCE(1)
  AUTOSTART
  SET(800)
FOLLOW(1)

/*
ONRED(300)
  RED(26)
DONE

ONAMBER(300)
  AMBER(26)
DONE

ONGREEN(300)
  GREEN(26)
DONE
*/

