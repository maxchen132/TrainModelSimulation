#include "defines.h"
#include "IODevice.h"

#ifndef IO_NO_HAL  // Only include if HAL is enabled

void halSetup() {
  // Create an I/O expander at VPIN 800, with 62 pins, at I2C address 0x65
  EXIOExpander::create(800, 62, 0x65);
}

#endif // IO_NO_HAL

