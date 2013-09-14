#include "servo.h"

#include <stdint.h>
#include <avr/io.h>

#if F_CPU != 8000000L
#error This will work only for 8MHz CPU frequency
#endif

#define SERVO_PRESCALER 8
#define SERVO_TICKS_PER_MS ((uint16_t)(F_CPU / (SERVO_PRESCALER * (uint16_t)1000)))
#define SERVO_NEUTRAL_POSITION_TICKS ((3 * SERVO_TICKS_PER_MS) / 2)
#define SERVO_PERIOD_TICKS (SERVO_PERIOD * SERVO_TICKS_PER_MS)

/// Calculate ((a << shift) / b) with correct rounding
/// a << (shift + 1) must fit into uint32_t
#define ROUNDED_DIVISION(a, b, shift) \
    (((((uint32_t)(a)) << ((shift) + 1)) / (b) + 1) >> 1)

void servo_init()
{
    // Timer1 (Generating servo PWM)
    TCCR1A =
        _BV(COM1A1) | // Clear OC1A on Compare Match, set OC1A at BOTTOM
        _BV(WGM11); // Fast PWM, counting to ICR1, ...
    TCCR1B =
        _BV(WGM12) | _BV(WGM13); // Fast PWM, counting to ICR1, continued
        // Timer disabled. The prescaler is set when servo output is enabled
    ICR1 = SERVO_PERIOD_TICKS; // setting the top value to 20ms

    DDRB |= _BV(PB1); // servo
}

void servo_enable()
{
    TCNT1 = SERVO_PERIOD_TICKS - 1; // We want a complete period of the servo to happen --
                                // including the first rising edge.

    TCCR1B |= _BV(CS11);
        // setting the prescaler to 8 => enabling timer.
}

void servo_disable()
{
    TCCR1B &= ~(_BV(CS10) | _BV(CS11) | _BV(CS12));
        // Clear the prescaler flags => disable timer
    PORTB &= ~_BV(PB1); // Set the output pin to zero.
}

/// Set the output value for the servo as signed integer from -127 to 127.
void servo_set(int8_t value)
{
    // OCR1A = SERVO_NEUTRAL_POSITION +
    //    (value * (SERVO_TICKS_PER_MS / 2)) / 127;
    uint16_t multiplier = ROUNDED_DIVISION(SERVO_TICKS_PER_MS / 2, INT8_MAX, 8);
    OCR1A = SERVO_NEUTRAL_POSITION_TICKS + ((value * multiplier) >> 8) - 1;
}
