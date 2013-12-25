#include <stdint.h>
#include <string.h>
#include <src_avr/robonet/robonet.h>
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

        robonetBuffer.address = ROBONET_MASTER_ADDRESS;
        for (int8_t i = robonetBuffer.length + 3; i >= 0; --i)
        {
            robonetBuffer.data[i] = ((uint8_t*)&robonetBuffer)[i];
        }
        robonetBuffer.data[robonetBuffer.length + 3] = status;
        robonetBuffer.length += 4;

        robonet_transmit();
    }
    return 0;
}

