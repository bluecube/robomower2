#include "turnigy.h"
#include "servo/servo.h"

#include <util/delay.h>

void delay()
{
    for (uint16_t i = 0; i < 1000; ++i)
        _delay_ms(1);
}

__attribute__ ((noinline, cold))
void calibrate_turningy_esc()
{
    servo_set16(SERVO_RANGE_TICKS);
    delay();
    delay();
    servo_set16(-SERVO_RANGE_TICKS);
    delay();
    servo_set16(0);
}
