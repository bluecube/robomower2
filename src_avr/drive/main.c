#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/atomic.h>
#include <stdint.h>
#include "servo/servo.h"
#include "build/drive.interface.h"

uint16_t latchedTicks;
uint8_t ticksHigh;

/// Return the measured distance in ticks, or
/// UINT8_MAX to indicate overflow.
/// Also reset the counter and clear the overflow flag.
uint8_t distance_travelled()
{
    uint8_t tmp = TCNT0;
    TCNT0 = 0;

    if (TIFR & _BV(TOV0))
    {
        // If there was an overflow
        TIFR |= _BV(TOV0); // Clearing flag by writing 1 into it? Datasheet seems to say so.
        return UINT8_MAX;
    }
    else
    {
        return tmp;
    }
}

int main()
{
    // Timer0 (counting encoder pulses)
    TCCR0 |= _BV(CS02) | _BV(CS01) | _BV(CS00); // external clock source for TCNT0, rising edge
    TIMSK |= _BV(TOIE0); // Enable overflow interrupt on TCNT0

    robonet_init();
    servo_init();
    servo_enable();
    sei(); // bzzzzzzzzz........

    while(1)
        layer2_communicate();
}

void handle_update_request(const struct update_request* in,
                           struct update_response* out)
{
    servo_set(in->speed);
    out->distance = latchedTicks;
}

void handle_latch_values_broadcast()
{
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE)
    {
        // Race condition!
        latchedTicks = TCNT0 | (ticksHigh << 8);
        TCNT0 = 0;
        ticksHigh = 0;
    }
}

ISR(TIMER0_OVF_vect)
{
    ++ticksHigh;
}
