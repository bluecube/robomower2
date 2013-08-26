################################ Configuration: ################################
CFLAGS+=-DF_CPU=8000000L
CFLAGS+=-DROBONET_OWN_ADDRESS=0x01
CFLAGS+=-DROBONET_DIRECTION_PORT=B
CFLAGS+=-DROBONET_DIRECTION_BIT=1
CFLAGS+=-DBAUD=200000L
CFLAGS+=-mmcu=atmega8
################################################################################

CC=avr-gcc
OBJCOPY=avr-objcopy

BUILD_DIR=build
GOAL=$(BUILD_DIR)/echo.hex

CFLAGS+=-Wall -Wextra
CFLAGS+=-Os -pipe -std=c99 -g

CFILES=main.c robonet_avr/robonet.c
#SFILES=
OFILES=$(addprefix $(BUILD_DIR)/,$(CFILES:.c=.o) $(SFILES:.s=.o))
DEPFILES = $(OFILES:.o=.d)

DO_MAKE_DIR=mkdir -p $(@D)

.PHONY: all
all: $(BUILD_DIR)/echo.hex

$(BUILD_DIR)/%.elf: $(OFILES)
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

$(BUILD_DIR)/%.o: %.c
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD_DIR)/%.o: %.s
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD_DIR)/%.d: %.c
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) -MM -MT $@ -MT $(@:.d=.o) -MF $@ $<

%.hex: %.elf
	$(OBJCOPY) -j .text -j .data -O ihex $< $@

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)

-include $(DEPFILES)
