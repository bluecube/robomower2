#include "robonet.h"

#include <util/setbaud.h>
#include <util/atomic.h>
#include <util/crc16.h>

volatile struct robonetPacket robonetBuffer;
volatile uint8_t status;

#define SYNC_BYTE 0x55

#define STATUS_WAITING_FOR_SYNC 0xff

#define CONCAT2_(A, B) A##B
#define CONCAT3_(A, B, C) A##B##C
#define CONCAT2(A, B) CONCAT2_(A, B)
#define CONCAT3(A, B, C) CONCAT3_(A, B, C)

#define DDR_DIRECTION CONCAT2(DDR, ROBONET_DIRECTION_PORT)
#define PORT_DIRECTION CONCAT2(PORT, ROBONET_DIRECTION_PORT)
#define NUMBER_DIRECTION CONCAT3(P, ROBONET_DIRECTION_PORT, ROBONET_DIRECTION_BIT)

void robonet_init()
{
    UCSRA = 0;
    UCSRB = _BV(RXCIE) | // recieve interrupt
        _BV(RXEN) | _BV(TXEN); // enable receive and transmit
    UCSRC = _BV(URSEL) | // register select -- needed for accessing UCSRC
        // asynchronous, no parity, 1 stop bit
        _BV(UCSZ1) | _BV(UCSZ0); // 8bit

    UBRRH = UBRRH_VALUE;
    UBRRL = UBRRL_VALUE;

    DDR_DIRECTION |= _BV(NUMBER_DIRECTION); // TXEN
    PORTD |= _BV(PD0); // enable pull-up on the RX pin
}

 __attribute__((const,always_inline))
static inline uint8_t crc_update(uint8_t crc, uint8_t data)
{
    if (__builtin_constant_p(crc) && __builtin_constant_p(data))
    {
        // Following is equivalent code for _crc_ibutton_update taken from AVR-libc documentation
        uint8_t i;

        crc = crc ^ data;
        for (i = 0; i < 8; i++)
        {
            if (crc & 0x01)
                crc = (crc >> 1) ^ 0x8C;
            else
                crc >>= 1;
        }

        return crc;
    }
    else
        return _crc_ibutton_update(crc, data);
}

/** Calculate correct CRC for the packet that is currently in the buffer. */
static uint8_t packet_crc()
{
    uint8_t crc = crc_update(0, SYNC_BYTE);
    uint8_t count = robonetBuffer.length + 2;
    uint8_t* data = (uint8_t*)(&robonetBuffer);
    for (uint8_t i = 0; i < count; ++i)
        crc = crc_update(crc, *data++);

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

    uint8_t lengthPlusThree = robonetBuffer.length + 3;

    if (ucsraCopy & _BV(FE))
        return ROBONET_FRAME_ERROR;
    if (ucsraCopy & _BV(DOR))
        return ROBONET_BYTE_OVERRUN_ERROR;
    if (statusCopy == STATUS_WAITING_FOR_SYNC || statusCopy < lengthPlusThree)
        return ROBONET_BUSY;

    status = STATUS_WAITING_FOR_SYNC;

    if (statusCopy > lengthPlusThree)
        return ROBONET_BUFFER_OVERRUN_ERROR;

    uint8_t crc = packet_crc();
    if (robonetBuffer.data[robonetBuffer.length] != crc)
        return ROBONET_CRC_ERROR;

    uint8_t deviceAddress = robonetBuffer.address & 0x0f;
    if (deviceAddress != ROBONET_OWN_ADDRESS && deviceAddress != ROBONET_BROADCAST_ADDRESS)
        return ROBONET_BUSY; // We ignore packets not belonging to us

    return ROBONET_OK;
}

uint8_t robonet_receive_complete()
{
    if (status != STATUS_WAITING_FOR_SYNC)
        return ROBONET_BUFFER_OVERRUN_ERROR;
    return ROBONET_OK;
}

void robonet_transmit()
{
    PORT_DIRECTION |= _BV(NUMBER_DIRECTION);

    UDR = SYNC_BYTE;
    while (!(UCSRA & _BV(UDRE)));

    uint8_t crc = crc_update(0, SYNC_BYTE);
    uint8_t count = robonetBuffer.length + 2;
    uint8_t* data = (uint8_t*)(&robonetBuffer);
    for (uint8_t i = 0; i < count; ++i)
    {
        uint8_t byte = *data++;
        UDR = byte;
        crc = crc_update(crc, byte);
        while (!(UCSRA & _BV(UDRE)));
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

    if (UCSRA & _BV(FE) || UCSRA & _BV(DOR))
        return;

    register uint8_t statusCopy = status;

    if (statusCopy == STATUS_WAITING_FOR_SYNC)
    {
        if (received != SYNC_BYTE)
            return;
    }
    else
    {
        ((uint8_t*)(&robonetBuffer))[statusCopy] = received;
    }

    status = statusCopy + 1;
}
