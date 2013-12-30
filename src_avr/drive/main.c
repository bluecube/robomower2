#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/atomic.h>
#include <stdint.h>
#include "servo/servo.h"
#include "build/drive.interface.h"

#define DIRECTION_CHANGE_ZERO_CYCLE_COUNT 4

union byteaccess
{
    uint16_t u16;
    uint8_t u8[2];
};

uint16_t odometryTicks;

uint16_t odometryTicksState;
uint16_t pidTicksState;

volatile uint8_t ticksHigh;

volatile int8_t requestedSpeed; // Units are ticks per SERVO_PERIOD
volatile int8_t requestedSpeedDirection;
volatile int8_t currentSpeedDirection;
volatile uint8_t needStopCycles;

volatile int8_t servoOutput;
volatile int16_t kP, kI;
volatile int16_t integratorLimit;
volatile int16_t integratorState;

int16_t clamp(int16_t val, int16_t min, int16_t max)
{
    if (val > max)
        return max;
    if (val < min)
        return min;
    return val;
}

/** Atomically read both lower and upper (extended by software) part of the encoder
 * tick counter and update the struct latched_value.
 * This function assumes that it finishes faster than is the period between encoder ticks
 * (at most one encoder tick may happen inside this function) and that it is executed with
 * interrupts enabled (because the counter high word is updated in an interrupt).
 * If these conditions are not met, then atomicity is lost and the low and high
 * bytes of the value might be desynchronized.
 *
 * This function is inline, because we want to avoid the indirect access to the state
 * variable and because there should be enough program space left on the device anyway. */
static uint16_t latch_encoder_ticks(uint16_t* restrict state)
{
    union byteaccess newState;

    newState.u8[0] = TCNT0;
    newState.u8[1] = ticksHigh;

    if (newState.u8[0] > TCNT0)
    {
        // there has been a timer overflow at timer 0
        // and it might have occured between reading TCNT0 and reading ticksHigh
        // we need to do it all over again.
        // The same problem will not repeat, because this function should execute
        // faster than a period between input ticks
        //
        // If there was only a single tick without overflow, we ignore it
        // and declare that the read happened before it (which is correct behavior).
        newState.u8[0] = TCNT0;
        newState.u8[1] = ticksHigh;
    }

    // Now everything is safe in newState

    uint16_t oldState = *state;
    *state = newState.u16;

    if (oldState <= newState.u16)
        return newState.u16 - oldState;
    else // An overflow occured
        return newState.u16 - oldState + UINT16_MAX;
}

int main()
{
    // Timer0 (counting encoder pulses)
    TCCR0 |= _BV(CS02) | _BV(CS01) | _BV(CS00); // external clock source for TCNT0, rising edge
    TIMSK |= _BV(TOIE0) | // Enable overflow interrupt on TCNT0
             _BV(TOIE1); // Enable overflow interrupt on TCNT1 (used by the servo library)

    layer2_init();
    servo_init();
    servo_enable();
    sei(); // bzzzzzzzzz........

    while(1)
        layer2_communicate();
}

void handle_update_request(const struct update_request* in,
                           struct update_response* out)
{
    int16_t newDirection;
    if (in->speed == 0)
    {
        requestedSpeed = 0;
        newDirection = 0;
    }
    else if (in->speed > 0)
    {
        requestedSpeed = in->speed;
        newDirection = 1;
    }
    else
    {
        requestedSpeed = -in->speed;
        newDirection = -1;
    }

    ATOMIC_BLOCK(ATOMIC_RESTORESTATE)
    {
        if (currentSpeedDirection != 0 && newDirection != currentSpeedDirection)
            needStopCycles = DIRECTION_CHANGE_ZERO_CYCLE_COUNT;
        requestedSpeedDirection = newDirection;
    }

    out->distance = odometryTicks;
}

void handle_params_request(const struct params_request* in)
{
    kP = in->kP;
    kI = in->kI;
    integratorLimit = in->integratorLimit;
}

void handle_latch_values_broadcast()
{
    int16_t ticks = latch_encoder_ticks(&odometryTicksState);
    if (currentSpeedDirection >= 0)
        odometryTicks = ticks;
    else
        odometryTicks = -ticks;
}

ISR(TIMER0_OVF_vect)
{
    ++ticksHigh;
}

ISR(TIMER1_OVF_vect, ISR_NOBLOCK)
{
    int16_t ticks = latch_encoder_ticks(&pidTicksState);

    if (needStopCycles > 0)
    {
        if (ticks == 0)
        {
            --needStopCycles;
            if (needStopCycles == 0)
                currentSpeedDirection = requestedSpeedDirection;
        }
        servo_set(0);
        return;
    }

    int16_t error = requestedSpeed - ticks;

    integratorState = clamp(integratorState + error, -integratorLimit, integratorLimit);

    int16_t tmpOutput = clamp((error * kP + integratorState * kI) / 256, 0, INT8_MAX);
    if (currentSpeedDirection >= 0)
        servo_set(tmpOutput);
    else
        servo_set(-tmpOutput);
}
