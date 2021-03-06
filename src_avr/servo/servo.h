#ifndef SRC_AVR_SERVO_SERVO_H
#define SRC_AVR_SERVO_SERVO_H

#include <stdint.h>

#include "preprocessor.h" // Included here because SERVO_RANGE_TICKS is part of the interface

void servo_init();
void servo_enable();
void servo_disable();

/** Set the output value for the servo as signed integer from -127 to 127. */
void servo_set(int8_t value);

/** Set servo value as a number from -SERVO_RANGE_TICKS to SERVO_RANGE_TICKS.
 * Range is not checked! */
void servo_set16(int16_t value);

#endif // SRC_AVR_SERVO_SERVO_H
