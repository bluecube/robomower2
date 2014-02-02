#include "turnigy.h"
#include "servo/servo.h"

#include <util/delay.h>

__attribute__ ((noinline, cold))
void calibrate_turningy_esc()
{
    servo_set16(SERVO_RANGE_TICKS);
    for (uint16_t i = 0; i < 10000; ++i)
        _delay_ms(1);
    servo_set16(-SERVO_RANGE_TICKS);
    for (uint16_t i = 0; i < 10000; ++i)
        _delay_ms(1);
    servo_set16(0);
    for (uint16_t i = 0; i < 10000; ++i)
        _delay_ms(1);
}
