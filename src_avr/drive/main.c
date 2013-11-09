#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdint.h>
#include "servo/servo.h"
#include "build/drive.interface.h"

#define lo8(x) (((uint8_t*)&(x))[0])
#define hi8(x) (((uint8_t*)&(x))[1])

struct latched_value
{
    uint16_t state;
    uint16_t previousState;
};

struct latched_value odometryTicks;

volatile uint8_t ticksHigh;

/** Atomically read both lower and upper (extended by software) part of the encoder
 * tick counter and update the struct latched_value.
 * This function assumes that it finishes faster than is the period between encoder ticks
 * (at most one encoder tick may happen inside this function) and that it is executed with
 * interrupts enabled (because the counter high word is updated in an interrupt).
 * If these conditions are not met, then atomicity is lost and the low and high
 * bytes of the value might be desynchronized.*/
static void latch_encoder_ticks(struct latched_value* out)
{
    uint8_t tmpTicks = TCNT0;
    uint8_t tmpTicksHigh = ticksHigh;

    if (tmpTicks > TCNT0)
    {
        // there has been a timer overflow at timer 0
        // and it might have occured between reading TCNT0 and reading ticksHigh
        // we need to do it all over again.
        // The same problem will not repeat, because this function should execute
        // faster than a period between input ticks
        //
        // If there was only a single tick without overflow, we ignore it
        // and declare that the read happened before it (which is correct behavior).
        tmpTicks = TCNT0;
        tmpTicksHigh = ticksHigh;
    }

    // Now everything is safe in tmpTicks and tmpTicksHigh!

    out->previousState = out->state;
    lo8(out->state) = tmpTicks;
    hi8(out->state) = tmpTicksHigh;
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
    out->distance = odometryTicks.state - odometryTicks.previousState;
}

void handle_latch_values_broadcast()
{
    latch_encoder_ticks(&odometryTicks);
}

ISR(TIMER0_OVF_vect)
{
    ++ticksHigh;
}
