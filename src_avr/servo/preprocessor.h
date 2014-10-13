#ifndef SRC_AVR_SERVO_PREPROCESSOR_H
#define SRC_AVR_SERVO_PREPROCESSOR_H

#if F_CPU != 8000000L
#error This will work only for 8MHz CPU frequency
#endif

#ifndef SERVO_PERIOD
/** Period of the servo signal in milliseconds.*/
#define SERVO_PERIOD 20
#endif

#define SERVO_PRESCALER 8
#define SERVO_TICKS_PER_MS (F_CPU / (SERVO_PRESCALER * (double)1000))
#define SERVO_NEUTRAL_POSITION_TICKS ((uint16_t)(1.5 * SERVO_TICKS_PER_MS))
#define SERVO_PERIOD_TICKS ((uint16_t)(SERVO_PERIOD * SERVO_TICKS_PER_MS))
#define SERVO_RANGE_TICKS ((uint16_t)(0.7 * SERVO_TICKS_PER_MS))


#endif // SRC_AVR_SERVO_PREPROCESSOR_H
