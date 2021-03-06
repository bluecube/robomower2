#include "servo.h"

#include <stdint.h>
#include <avr/io.h>

#include "preprocessor.h"

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
    OCR1A = SERVO_NEUTRAL_POSITION_TICKS;
    TCCR1B |= _BV(CS11); // setting the prescaler to 8 => enabling timer.
}

void servo_disable()
{
    TCCR1B &= ~(_BV(CS10) | _BV(CS11) | _BV(CS12));
        // Clear the prescaler flags => disable timer
    PORTB &= ~_BV(PB1); // Set the output pin to zero.
}

void servo_set(int8_t value)
{
    /* This function contains a hackish way to do:

    OCR1A = SERVO_NEUTRAL_POSITION_TICKS +
        (value * SERVO_RANGE_TICKS) / 127;

    while avoiding division and 32bit multiplication.
    The result is not optimal, but it's much better than what the compiler
    would generate by itself. */

    int16_t multiplierHi = ROUNDED_DIVISION(SERVO_RANGE_TICKS, INT8_MAX, 8) >> 8;
    int16_t multiplierLo = ROUNDED_DIVISION(SERVO_RANGE_TICKS, INT8_MAX, 8) & 0xFF;

    // We're doing (value * multiplier) >> 8, while avoiding 32bit multiplication
    int16_t tmp = ((multiplierLo * value) >> 8) + (multiplierHi * value);
    servo_set16(tmp);
}

void servo_set16(int16_t value)
{
    OCR1A = SERVO_NEUTRAL_POSITION_TICKS + value - 1;
}
