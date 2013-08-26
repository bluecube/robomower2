#include "robonet.h"

#include <util/setbaud.h>
#include <util/atomic.h>
#include <util/crc16.h>

volatile struct robonetPacket robonetBuffer;
volatile uint8_t status;

#define CONCAT2_(A, B) A##B
#define CONCAT3_(A, B, C) A##B##C
#define CONCAT2(A, B) CONCAT2_(A, B)
#define CONCAT3(A, B, C) CONCAT3_(A, B, C)

#define DDR_DIRECTION CONCAT2(DDR, ROBONET_DIRECTION_PORT)
#define PORT_DIRECTION CONCAT2(PORT, ROBONET_DIRECTION_PORT)
#define NUMBER_DIRECTION CONCAT3(P, ROBONET_DIRECTION_PORT, ROBONET_DIRECTION_BIT)

void robonet_init()
{
    UCSRA = _BV(MPCM); // multiprocessor mode
    UCSRB = _BV(RXCIE) | _BV(TXCIE) | _BV(UDRIE) | // all interrupts
        _BV(RXEN) | _BV(TXEN) | // enable receive and transmit
        _BV(UCSZ2); // first part of 9bit setting.
    UCSRC = _BV(URSEL) | // register select -- needed for accessing UCSRC
        // asynchronous, no parity, 1 stop bit
        _BV(UCSZ1) | _BV(UCSZ0); // 9bit, continued

    UBRRH = UBRRH_VALUE;
    UBRRL = UBRRL_VALUE;

    DDR_DIRECTION |= _BV(NUMBER_DIRECTION); // TXEN
}

/** Calculate correct CRC for the packet that is currently in the buffer. */
static uint8_t packet_crc()
{
    uint8_t crc = 0;
    for (int i = 0; i < robonetBuffer.length + 3; ++i)
        crc = _crc_ibutton_update(crc, ((uint8_t*)(&robonetBuffer))[i]);

    return crc;
}

uint8_t robonet_receive()
{
    uint8_t ucsraCopy;
    uint8_t statusCopy;

    ATOMIC_BLOCK(ATOMIC_RESTORESTATE)
    {
        ucsraCopy = UCSRA;
        statusCopy = status;

        UCSRA &= ~_BV(FE);
        UCSRA &= ~_BV(DOR);
    }

    if (ucsraCopy & _BV(FE))
    {
        status = 0;
        return ROBONET_FRAME_ERROR;
    }
    else if (ucsraCopy & _BV(DOR))
    {
        status = 0;
        return ROBONET_BYTE_OVERRUN_ERROR;
    }
    else if (statusCopy > robonetBuffer.length + 3)
    {
        status = 0;
        return ROBONET_BUFFER_OVERRUN_ERROR;
    }
    else if (statusCopy < 3 || statusCopy < robonetBuffer.length + 3)
        return ROBONET_BUSY;

    uint8_t crc = packet_crc();
    if (robonetBuffer.data[robonetBuffer.length] != crc)
    {
        status = 0;
        return ROBONET_CRC_ERROR;
    }

    status = 0;
    return ROBONET_OK;
}

uint8_t robonet_receive_complete()
{
    if (status != 0)
        return ROBONET_BUFFER_OVERRUN_ERROR;
    return ROBONET_OK;
}

void robonet_transmit()
{
    uint8_t crc = packet_crc();
    robonetBuffer.data[robonetBuffer.length] = crc;

    status = 1;
    PORT_DIRECTION |= _BV(NUMBER_DIRECTION);
    UCSRB |= _BV(TXB8);
    UDR = robonetBuffer.address;
}

ISR(USART_RXC_vect)
{
    if (UCSRA & _BV(FE) || UCSRA & _BV(DOR))
        return;

    uint8_t received = UDR;

    if (status == 0)
    {
        uint8_t targetAddress = received & 0x0f;
        if (targetAddress != ROBONET_OWN_ADDRESS && targetAddress != ROBONET_BROADCAST_ADDRESS)
            return;

        UCSRA &= ~_BV(MPCM);
    }

    ((uint8_t*)(&robonetBuffer))[status] = received;
    ++status;

    if (status == robonetBuffer.length + 3)
        UCSRA |= _BV(MPCM);
}

ISR(USART_UDRE_vect)
{
    if (status >= robonetBuffer.length + 3)
        return; // wait for the last byte to be finished and then terminate the
                // transmission in the TXC vector.

    UCSRB &= ~_BV(TXB8);
    UDR = ((uint8_t *)(&robonetBuffer))[status];
    ++status;
}

ISR(USART_TXC_vect)
{
    PORT_DIRECTION &= ~_BV(NUMBER_DIRECTION);
    status = 0;
}
