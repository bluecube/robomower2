#include <stdint.h>
#include <string.h>
#include <robonet/robonet.h>
#include <avr/interrupt.h>

int main()
{
    robonet_init();
    sei();

    while(1)
    {
        uint8_t status = robonet_receive();
        if (status == ROBONET_BUSY)
            continue;

        memmove((void*)robonetBuffer.data, (void*)&robonetBuffer, robonetBuffer.length + 3);
        robonetBuffer.length += 4;
        robonetBuffer.data[robonetBuffer.length - 1] = status;

        robonet_transmit();
    }
    return 0;
}

