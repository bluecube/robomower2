#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/atomic.h>
#include <stdint.h>
#include "turnigy.h"

// drive interface must be included before servo
#include "build/drive.interface.h"
#define SERVO_PERIOD (1000.0 / PID_FREQUENCY)

#include "servo/servo.h"

#define DIRECTION_CHANGE_ZERO_CYCLE_COUNT 4
#define SAFETY_TIMEOUT ((uint8_t)(1000 / SERVO_PERIOD))

#if PARAMS_REQUEST_KP_MULTIPLIER == PARAMS_REQUEST_KI_MULTIPLIER && PARAMS_REQUEST_KP_MULTIPLIER == PARAMS_REQUEST_KD_MULTIPLIER
    #define PID_MULTIPLIER PARAMS_REQUEST_KP_MULTIPLIER
#else
    #error "Different multipliers for kP, kI and kD"
#endif

union byteaccess
{
    uint16_t u16;
    uint8_t u8[2];
};

uint16_t odometryTicks;

uint16_t odometryTicksState;
uint8_t pidTicksState;

volatile uint8_t ticksHigh;

// The following variables don't need to be volatile, since these are
// always set within ATOMIC block, or from within an interrupt
int8_t requestedSpeed; // Units are ticks per SERVO_PERIOD
int8_t requestedDirection;
int8_t currentDirection;
uint8_t needStopCycles;
uint8_t lastTicks[DERIVATIVE_SMOOTHING + 1];
int16_t kP, kI, kD;
int16_t integratorState;
uint8_t safetyCounter;

struct debug_response debugData;

int16_t clamp(int16_t val, int16_t min, int16_t max)
{
    if (val > max)
        return max;
    if (val < min)
        return min;
    return val;
}

/** Atomically read both lower and upper (extended by software) part of the encoder
 * tick counter and the sensor pin value and return the number of ticks since the last call.
 * Parameter state stores the state of the tick counter that corresponds to the value returned.
 *
 * Here we use a (kind of) dirty trick to count both rising and falling edges of the
 * sensor signal while only using the counter that can count only falling edges.
 * We treat the each count from the counter as 2 ticks and fill the lower bit from
 * the current state of the sensor pin.
 *
 * This function assumes that it finishes faster than is the period between sensor
 * state changes (at most one change may happen inside this function) and that it
 * is executed with interrupts enabled (because the counter high word is updated
 * in an interrupt). If these conditions are not met, then atomicity is lost and
 * the low and high bytes of the value might be desynchronized. */
static uint16_t latch_encoder_ticks16(uint16_t* restrict state)
{
    uint8_t pindCopy = PIND;
    union byteaccess newState;
    newState.u8[0] = TCNT0;
    newState.u8[1] = ticksHigh;

    uint8_t pindCopy2 = PIND; // This is the point that decides if there was a change.

    uint8_t overflowBit = pindCopy & ~pindCopy2;
    if (overflowBit & _BV(PD4)) // the old bit at PD4 was true and the new one is false
    {
        // The sensor value has changed and the change might have occured between
        // reading the three parts. We need to do it all over again.
        // The same problem will not repeat, because this function should execute
        // faster than a period between input ticks
        //
        // If there was only a single change without counter tick, we ignore it
        // and declare that the read happened before it (which is correct behavior).
        pindCopy = pindCopy2;
        newState.u8[0] = TCNT0;
        newState.u8[1] = ticksHigh;
    }

    // Now everything that could change is safe in pindCopy and newState

    // Shift the newState up to fit the extra bit in
    newState.u16 <<= 1;
    if (pindCopy & _BV(PD4))
        newState.u8[0] |= 1;

    uint16_t oldState = *state;
    *state = newState.u16;

    uint16_t ret = newState.u16 - oldState;
    if (oldState > newState.u16)
        ret += UINT16_MAX;
    return ret;
}

/** Atomically read both lower and upper (extended by software) part of the encoder
 * tick counter and return the number of ticks since the last call.
 * Parameter state stores the state of the tick counter that corresponds to the value returned.
 *
 * Works almost exactly like latch_encoder_ticks16, but trades maximal number of encoder
 * ticks between state updates for speed and code size (both should be inlined).
 *
 * @see latch_encoder_ticks16() and the comments inside. */
static uint8_t latch_encoder_ticks8(uint8_t* restrict state)
{
    uint8_t pindCopy = PIND;
    uint8_t newState = TCNT0;

    uint8_t pindCopy2 = PIND;

    uint8_t overflowBit = pindCopy & ~pindCopy2;
    if (overflowBit & _BV(PD4))
    {
        pindCopy = pindCopy2;
        newState = TCNT0;
    }

    newState <<= 1;
    if (pindCopy & _BV(PD4))
        newState |= 1;

    uint8_t oldState = *state;
    *state = newState;

    uint8_t ret = newState - oldState;
    if (oldState > newState)
        ret += UINT8_MAX;
    return ret;
}

int main()
{
    // Timer0 (counting encoder pulses)
    TCCR0 |= _BV(CS02) | _BV(CS01); // external clock source for TCNT0, falling edge
    TIMSK |= _BV(TOIE0) | // Enable overflow interrupt on TCNT0
             _BV(TOIE1); // Enable overflow interrupt on TCNT1 (used by the servo library)

    layer2_init();
    servo_init();
    servo_enable();

    //calibrate_turningy_esc(); // This has to be used without interrupts

    sei(); // bzzzzzzzzz........

    while(1)
        layer2_communicate();
}

void handle_update_request(const struct update_request* in,
                           struct update_response* out)
{
    int16_t newDirection;
    int8_t newSpeed;
    if (in->speed == 0)
    {
        newSpeed = 0;
        newDirection = 0;
    }
    else if (in->speed > 0)
    {
        newSpeed = in->speed;
        newDirection = 1;
    }
    else
    {
        newSpeed = -in->speed;
        newDirection = -1;
    }

    ATOMIC_BLOCK(ATOMIC_RESTORESTATE)
    {
        if (currentDirection != 0 && newDirection != currentDirection)
            needStopCycles = DIRECTION_CHANGE_ZERO_CYCLE_COUNT;
        else
            currentDirection = newDirection;
        requestedSpeed = newSpeed;
        requestedDirection = newDirection;
        safetyCounter = SAFETY_TIMEOUT;
    }

    out->distance = odometryTicks;
}

void handle_params_request(const struct params_request* in)
{
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE)
    {
        kP = in->kP;
        kI = in->kI;
        kD = in->kD;
    }
}

void handle_latch_values_broadcast()
{
    int16_t ticks = latch_encoder_ticks16(&odometryTicksState);
    if (currentDirection >= 0)
        odometryTicks = ticks;
    else
        odometryTicks = -ticks;
}

void handle_debug_request(struct debug_response* out){
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE)
    {
        *out = debugData;
        debugData.currentTick = 0;
    }
}

void stop()
{
    servo_set(0);
    integratorState = 0;
    for (int8_t i = 0; i <= DERIVATIVE_SMOOTHING; ++i)
        lastTicks[i] = 0;
}

ISR(TIMER0_OVF_vect)
{
    ++ticksHigh;
}

ISR(TIMER1_OVF_vect, ISR_NOBLOCK)
{
    if (safetyCounter == 0)
    {
        stop();
        return;
    }
    --safetyCounter;

    int8_t ticks = latch_encoder_ticks8(&pidTicksState);

    int8_t needStopCyclesCopy = needStopCycles;
    if (needStopCyclesCopy > 0)
    {
        if (ticks == 0)
        {
            needStopCyclesCopy--;
            needStopCycles = needStopCyclesCopy;
            if (needStopCyclesCopy == 0)
                currentDirection = requestedDirection;
        }
        else
            needStopCycles = DIRECTION_CHANGE_ZERO_CYCLE_COUNT;

        stop();
        return;
    }

    if (currentDirection == 0)
    {
        stop();
        return;
    }

    int16_t error = requestedSpeed - ticks;
    int16_t difference = lastTicks[0] - ticks;
    for (int8_t i = 0; i < DERIVATIVE_SMOOTHING; ++i)
        lastTicks[i] = lastTicks[i + 1];
    lastTicks[DERIVATIVE_SMOOTHING] = ticks;

    if (debugData.currentTick < sizeof(debugData.ticks) / sizeof(debugData.ticks[0]))
    {
        debugData.ticks[debugData.currentTick] = difference;
        ++debugData.currentTick;
    }

    integratorState = clamp(integratorState + error,
                            -SERVO_RANGE_TICKS, SERVO_RANGE_TICKS);
    int16_t tmpOutput = error * kP +
                        integratorState * kI +
                        (difference * kD) / (DERIVATIVE_SMOOTHING + 1);
    tmpOutput = clamp(tmpOutput / PID_MULTIPLIER, 0, SERVO_RANGE_TICKS);
    if (currentDirection < 0)
        tmpOutput = -tmpOutput;

    servo_set16(tmpOutput);
}
