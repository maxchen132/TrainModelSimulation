#include "defines.h"
#include "IODevice.h"
#include "Sensors.h"

#ifndef IO_NO_HAL

//-----------------------------------------------------------------------------
// 1) VPIN definitions
//    Choose an analog VPIN (>= 4000 typically) and
//    a digital VPIN for the alarm sensor (>=0 && < 4000).
static const int VPIN_ACS_0 = A0;   // analog‐input VPIN
static const int VPIN_ACS_0_ALARM = 144;    // digital VPIN for the threshold alarm

static const int VPIN_ACS_1 = A1;   // analog‐input VPIN
static const int VPIN_ACS_1_ALARM = 145;    // digital VPIN for the threshold alarm

static const int VPIN_ACS_2 = A2;   // analog‐input VPIN
static const int VPIN_ACS_2_ALARM = 146;    // digital VPIN for the threshold alarm

// 2) Trigger threshold (0–1023)
static const int THRESHOLD = 90;

// Forward‐declare our polling function
static void sampleACS();

void halSetup() {
  // I/O expander
  EXIOExpander::create(800, 62, 0x65);

  // Create a digital sensor bean in DCC-EX on VPIN_ACS_0_ALARM
  //     The third argument is "active low" flag: 1 = sensor pulls pin LOW when active,
  //     0 = sensor drives HIGH when active.  Adjust if needed.
  Sensor::create(VPIN_ACS_0_ALARM, VPIN_ACS_0_ALARM, 1);
  Sensor::create(VPIN_ACS_1_ALARM, VPIN_ACS_1_ALARM, 1);
  Sensor::create(VPIN_ACS_2_ALARM, VPIN_ACS_2_ALARM, 1);

  // Schedule our sampler every 100 ms
  UserAddin::create(sampleACS, 100);
}

//-----------------------------------------------------------------------------
// 3) Poll the ACS712 (analog) and drive the Sensor (digital)

static void sampleACS() {
  // read 0–1023 from the analog VPIN
  int raw = IODevice::readAnalogue(VPIN_ACS_0);

  // compare to threshold
  bool over = (raw > THRESHOLD);

  // write the digital sensor pin accordingly:
  // if over == true, set VPIN_ACS_0_ALARM HIGH (inactive low sensors)
  // if over == false, set it LOW
  IODevice::write(VPIN_ACS_0_ALARM, over ? 0 : 1);

  // optionally you can log to the console for debugging:
  DIAG(F("ACS raw=%d  alarm=%d"), raw, over?1:0);

  // read 0–1023 from the analog VPIN
  raw = IODevice::readAnalogue(VPIN_ACS_1);

  // compare to threshold
  over = (raw > THRESHOLD);

  // write the digital sensor pin accordingly:
  // if over == true, set VPIN_ACS_0_ALARM HIGH (inactive low sensors)
  // if over == false, set it LOW
  IODevice::write(VPIN_ACS_1_ALARM, over ? 0 : 1);

  // optionally you can log to the console for debugging:
  DIAG(F("ACS raw=%d  alarm=%d"), raw, over?1:0);

  // read 0–1023 from the analog VPIN
  raw = IODevice::readAnalogue(VPIN_ACS_2);

  // compare to threshold
  over = (raw > THRESHOLD);

  // write the digital sensor pin accordingly:
  // if over == true, set VPIN_ACS_0_ALARM HIGH (inactive low sensors)
  // if over == false, set it LOW
  IODevice::write(VPIN_ACS_2_ALARM, over ? 0 : 1);

  // optionally you can log to the console for debugging:
  DIAG(F("ACS raw=%d  alarm=%d"), raw, over?1:0);
}

#endif // IO_NO_HAL
