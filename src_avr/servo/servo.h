#ifndef SRC_AVR_SERVO_SERVO_H
#define SRC_AVR_SERVO_SERVO_H

#include <stdint.h>

#ifndef SERVO_PERIOD
// Period of the servo signal in milliseconds.
#define SERVO_PERIOD 20
#endif

void servo_init();
void servo_enable();
void servo_disable();
void servo_set(int8_t value);

#endif // SRC_AVR_SERVO_SERVO_H
