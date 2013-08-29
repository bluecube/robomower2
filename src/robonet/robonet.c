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
    //UCSRA = _BV(MPCM); // multiprocessor mode
    UCSRB = _BV(RXCIE) | // recieve interrupt
        _BV(RXEN) | _BV(TXEN) | // enable receive and transmit
        _BV(UCSZ2); // first part of 9bit setting.
    UCSRC = _BV(URSEL) | // register select -- needed for accessing UCSRC
        // asynchronous, no parity, 1 stop bit
        _BV(UCSZ1) | _BV(UCSZ0); // 9bit, continued

    UBRRH = UBRRH_VALUE;
    UBRRL = UBRRL_VALUE;

    DDR_DIRECTION |= _BV(NUMBER_DIRECTION); // TXEN
    PORTD |= _BV(PD0); // enable pull-up ont the RX pin

    //DDRC |= _BV(PC5);
    //PORTC |= _BV(PC5);
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
    uint8_t crc = 0;

    PORT_DIRECTION |= _BV(NUMBER_DIRECTION);
    UCSRB |= _BV(TXB8);

    for (int i = 0; i < robonetBuffer.length + 2; ++i)
    {
        uint8_t byte = ((uint8_t *)(&robonetBuffer))[i];
        UDR = byte;
        crc = _crc_ibutton_update(crc, byte);

        while (!(UCSRA & _BV(UDRE)));
        UCSRB &= ~_BV(TXB8);
    }

    UDR = crc;
    UCSRA |= _BV(TXC);
    //a race condition right here -- if the code gets interrupted between
    //setting UDR and TXC, then the txc might be cleared after all the data have
    //been shifted out and the following loop might get stuck forever.
    //This will not be a problem if interrupts are short
    while (!(UCSRA & _BV(TXC)));

    PORT_DIRECTION &= ~_BV(NUMBER_DIRECTION);
}

ISR(USART_RXC_vect)
{
    uint8_t received = UDR;
    //PORTC ^= _BV(PC5);

    if (UCSRA & _BV(FE) || UCSRA & _BV(DOR))
        return;

    register uint8_t statusCopy = status;

    if (statusCopy == 0)
    {
        uint8_t targetAddress = received & 0x0f;
        if (targetAddress != ROBONET_OWN_ADDRESS && targetAddress != ROBONET_BROADCAST_ADDRESS)
        {
            return;
        }

        UCSRA &= ~_BV(MPCM);
    }

    ((uint8_t*)(&robonetBuffer))[statusCopy] = received;
    ++statusCopy;

    if (statusCopy >= robonetBuffer.length + 3)
        UCSRA |= _BV(MPCM);

    status = statusCopy;
    // TODO: What happens when a new packet is received when older packet was not
    // handled? Is this taken care of?
}
