################################ Configuration: ################################
F_CPU = 8000000
MCU = atmega8
################################################################################

CC=avr-gcc
OBJCOPY=avr-objcopy

ifndef I2C_ADDRESS
$(error I2C address must be passed to make)
endif

BUILD_DIR=build
GOAL=$(BUILD_DIR)/driver.hex

CFLAGS+=-DF_CPU=$(F_CPU)
CFLAGS+=-DI2C_ADDRESS=$(I2C_ADDRESS)
CFLAGS+=-mmcu=$(MCU)
CFLAGS+=-Wall -Wextra
CFLAGS+=-Os

CFILES=main.c
OFILES=$(addprefix $(BUILD_DIR)/,$(CFILES:.c=.o))
DEPFILES = $(OFILES:.o=.d)

DO_MAKE_DIR=mkdir -p $(@D)

.PHONY: all
all: $(BUILD_DIR)/drive.hex

$(BUILD_DIR)/%.elf: $(OFILES)
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

$(BUILD_DIR)/%.o: %.c
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) -c -o $@ $^

$(BUILD_DIR)/%.d: %.c
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) -MM -MT $@ -MT $(@:.d=.o) -MF $@ $^

%.hex: %.elf
	$(OBJCOPY) -j .text -j .data -O ihex $< $@

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)
	$(MAKE) -C test clean

-include $(DEPFILES)
