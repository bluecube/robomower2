#include <stdint.h>
#include <src_avr/robonet/robonet.h>
#include <src_avr/servo/servo.h>
#include <avr/interrupt.h>
#include <avr/io.h>

int main()
{
    robonet_init();
    servo_init();
    sei();

    servo_enable();

    while(1)
    {
        uint8_t status = robonet_receive();
        if (status == ROBONET_BUSY)
            continue;

        servo_set((int8_t)robonetBuffer.data[0]);
        *(int16_t*)&robonetBuffer.data[0] = OCR1A;
        robonetBuffer.data[2] = status;

        robonetBuffer.address = 0;
        robonetBuffer.length = 3;

        robonet_transmit();
    }
    return 0;
}

