#include <avr/io.h>
#include <stdint.h>

#if F_CPU != 8000000L
#error This will work only for 8MHz CPU frequency
#endif

#ifndef I2C_ADDRESS
#error I2C address must be set!
#endif

#define SERVO_PRESCALER 8
#define SERVO_TICKS_PER_MS ((uint16_t)(F_CPU / (SERVO_PRESCALER * (uint16_t)1000)))
#define SERVO_NEUTRAL_POSITION ((3 * SERVO_TICKS_PER_MS) / 2)
#define SERVO_PERIOD (20 * SERVO_TICKS_PER_MS)

void sensor_enable()
{
    PORTD |= _BV(PD3); // enable sensor power
    PORTD |= _BV(PD4); // enable pull up resistor
}

void sensor_disable()
{
    PORTD &= ~_BV(PD3); // disable sensor power
    PORTD &= ~_BV(PD4); // disable pull up resistor
}

/// Set the output value for the servo as signed integer from -127 to 127.
void servo_set(int16_t value)
{
    OCR1A = SERVO_NEUTRAL_POSITION + (value * (SERVO_TICKS_PER_MS / 2)) / 127;
}

void servo_enable(int16_t value)
{
    servo_set(value);

    TCNT1 = SERVO_PERIOD - 1; // We want a complete period of the servo to happen --
                              // including the first rising edge.

    TCCR1B |= _BV(CS10) | _BV(CS11);
        // setting the prescaler to 8 => enabling timer.
}

void servo_disable()
{
    TCCR1B &= _BV(CS10) | _BV(CS11) | _BV(CS12);
    PORTB &= ~_BV(PB1); // Set the output pin to zero.
}

void setup()
{
    // Output ports:
    DDRB |= _BV(PB1); // servo
    DDRD |= _BV(PD3); // snsor power

    // Timer0 (counting encoder pulses)
    TCCR0 |= _BV(CS02) | _BV(CS01) | _BV(CS00); // external clock source, rising

    // Timer1 (Generating servo PWM)
    TCCR1A =
        _BV(COM1A1) | // Clear OC1A on Compare Match, set OC1A at BOTTOM
        _BV(WGM11); // Fast PWM, counting to ICR1, ...
    TCCR1B =
        _BV(WGM12) | _BV(WGM13); // Fast PWM, counting to ICR1, continued
        // Timer disabled. The prescaler is set when servo output is enabled
    ICR1 = SERVO_PERIOD - 1; // setting the top value to 20ms

    // I2C communication
    TWAR = I2C_ADDRESS << 1;
    TWCR =
        _BV(TWEA) | // Enable acknowledge
        _BV(TWEN) | // enable
        _BV(TWIE); // enable interrupts
}


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

