#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdint.h>
#include <robonet/robonet.h>
#include <../servo/servo.h>

uint16_t latchedTicks;

void motor_enable()
{
    PORTD |= _BV(PD4); // Enable sensor power
    servo_enable();
}

void motor_disable()
{
    servo_disable();
    PORTD &= ~_BV(PD4); // disable sensor power
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

void init()
{
    // Output ports:
    DDRD |= _BV(PD4); // sensor power

    // Timer0 (counting encoder pulses)
    TCCR0 |= _BV(CS02) | _BV(CS01) | _BV(CS00); // external clock source, rising

    robonet_init();
}

int main()
{
    init();
    sei(); // bzzzzzzzzz........

    while(1)
        layer2_communicate();
}
