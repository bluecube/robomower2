ifndef ROBONET_OWN_ADDRESS
    $(error ROBONET_OWN_ADDRESS must be set)
endif
ifndef ROBONET_DIRECTION_PORT
    $(error ROBONET_DIRECTION_PORT must be set)
endif
ifndef ROBONET_DIRECTION_BIT
    $(error ROBONET_DIRECTION_BIT must be set)
endif

# Default settings
F_CPU?=8000000L
BAUD?=38400
MCU?=atmega8

AVRDUDE_PORT?=/dev/ttyUSB0
AVRDUDE_COMMAND?=avrdude -p $(MCU) -c buspirate -P $(AVRDUDE_PORT)

CC=avr-gcc
OBJCOPY?=avr-objcopy

BUILD_DIR=build
GOAL_FILE=$(BUILD_DIR)/$(GOAL)-$(ROBONET_OWN_ADDRESS).hex

CFLAGS+=-DF_CPU=$(F_CPU)
CFLAGS+=-DROBONET_OWN_ADDRESS=$(ROBONET_OWN_ADDRESS)
CFLAGS+=-DROBONET_DIRECTION_PORT=$(ROBONET_DIRECTION_PORT)
CFLAGS+=-DROBONET_DIRECTION_BIT=$(ROBONET_DIRECTION_BIT)
CFLAGS+=-DBAUD=$(BAUD)
CFLAGS+=-mmcu=$(MCU)
CFLAGS+=-Wall -Wextra
CFLAGS+=-flto
CFLAGS+=-Os -pipe -std=c99 -g

OFILES=$(addprefix $(BUILD_DIR)/,$(CFILES:.c=.o) $(SFILES:.s=.o))
DEPFILES = $(OFILES:.o=.d)

DO_MAKE_DIR=mkdir -p $(@D)

.PHONY: all
all: $(GOAL_FILE)

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

$(BUILD_DIR)/%.d: %.s
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) -MM -MT $@ -MT $(@:.d=.o) -MF $@ $<

%.hex: %.elf
	$(OBJCOPY) -j .text -j .data -O ihex $< $@

.PHONY: upload
upload: $(GOAL_FILE)
	$(AVRDUDE_COMMAND) -U flash:w:$(GOAL_FILE):i

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)

-include $(DEPFILES)
