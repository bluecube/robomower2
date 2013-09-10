/** \file
 * Implementation of Martin Locker's 8 bit RoboNet protocol for RS485.
 */

#ifndef SRC_AVR_ROBONET_ROBONET_H
#define SRC_AVR_ROBONET_ROBONET_H

#include <avr/io.h>
#include <stdint.h>

#define ROBONET_MAX_DATA_SIZE 15

#define ROBONET_OK 0
#define ROBONET_BUSY 1
#define ROBONET_CRC_ERROR 2
#define ROBONET_FRAME_ERROR 3
#define ROBONET_BYTE_OVERRUN_ERROR 4
#define ROBONET_BUFFER_OVERRUN_ERROR 5

#define ROBONET_MASTER_ADDRESS 0x0
#define ROBONET_BROADCAST_ADDRESS 0xf

#ifndef ROBONET_OWN_ADDRESS
#error ROBONET_OWN_ADDRESS must be defined!
#endif

#ifndef ROBONET_DIRECTION_PORT
#error ROBONET_DIRECTION_PORT must be defined!
#endif
#ifndef ROBONET_DIRECTION_BIT
#error ROBONET_DIRECTION_BIT must be defined!
#endif

struct robonetPacket
{
    uint8_t address;
    uint8_t length;
    uint8_t data[ROBONET_MAX_DATA_SIZE + 1];
};

extern volatile struct robonetPacket robonetBuffer;

/** Initialize the robonet protocol, prepare the usart hardware. */
void robonet_init();

/** Attempt to receive a single packet. Non-blocking.
 * @return
 * * ROBONET_OK if a packet is correctly received and waiting in the buffer
 * * ROBONET_BUSY if a complete packet was not received yet.
 * * ROBONET_*_ERROR if there was a problem with receiving. */
uint8_t robonet_receive();

/** Checks, if the buffer was written a new received data since the last robonet_receive.
 * This function is not necessary, but provides another point of error detection.
 * @return
 *  * ROBONET_OK No writes to the buffer were performed
 *  * ROBONET_BUFFER_OVERRUN_ERROR Received data were damaged and should not be used. */
uint8_t robonet_check_buffer_overrun();

/** Start transmission of data in the buffer. Non-blocking. */
void robonet_transmit();

#endif //SRC_AVR_ROBONET_ROBONET_H
