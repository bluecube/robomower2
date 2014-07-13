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
ROBONET_PATH?=robonet
override ROBONET_OWN_ADDRESS:=$(shell printf '%\#04x' $(ROBONET_OWN_ADDRESS))

AVRDUDE_PORT?=/dev/ttyUSB0
AVRDUDE_COMMAND?=avrdude -p $(MCU) -c buspirate -P $(AVRDUDE_PORT)

CC=avr-gcc
OBJCOPY?=avr-objcopy
OBJDUMP?=avr-objdump

BUILD_DIR=build
GOAL_FILE=$(BUILD_DIR)/$(GOAL)-$(ROBONET_OWN_ADDRESS).hex

CFILES+=$(ROBONET_PATH)/robonet.c

CFLAGS+=-DF_CPU=$(F_CPU)
CFLAGS+=-DROBONET_OWN_ADDRESS=$(ROBONET_OWN_ADDRESS)
CFLAGS+=-DROBONET_DIRECTION_PORT=$(ROBONET_DIRECTION_PORT)
CFLAGS+=-DROBONET_DIRECTION_BIT=$(ROBONET_DIRECTION_BIT)
CFLAGS+=-DBAUD=$(BAUD)
CFLAGS+=-mmcu=$(MCU)
CFLAGS+=-Wall -Wextra
CFLAGS+=-frename-registers -fweb -ftracer
CFLAGS+=-O3 -pipe -std=c99 -g

MAKEFILE_PATH:=$(dir $(lastword $(MAKEFILE_LIST)))
LAYER2_SCRIPT:=$(MAKEFILE_PATH)/../src_python/layer2/generator.py

OFILES:=$(addprefix $(BUILD_DIR)/,$(addsuffix .o,$(CFILES) $(SFILES)) $(addsuffix .c.o,$(IFFILES)))
DEPFILES:=$(OFILES:.o=.d)

DO_MAKE_DIR=mkdir -p $(@D)

# <HACK HACK HACK HACKITY HACK>
CFILES_WHOPR=$(CFILES) $(addprefix $(BUILD_DIR)/,$(addsuffix .c,$(IFFILES)))
CFLAGS+=-fwhole-program
WHOPR=$(BUILD_DIR)/whopr.c
OFILES:=$(WHOPR:.c=.c.o) $(addprefix $(BUILD_DIR)/,$(addsuffix .o,$(SFILES)))
DEPFILES+=$(WHOPR:.c=.c.d)
.DEFAULT_GOAL:=all
$(WHOPR): $(CFILES_WHOPR)
	$(DO_MAKE_DIR)
	echo > $@
	for file in $^ ; do echo "#include \"../$$file\"" >> $@ ; done
# </HACK HACK HACK HACKITY HACK>

.PHONY: all
all: $(GOAL_FILE)

$(BUILD_DIR)/%.elf: $(OFILES)
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

$(BUILD_DIR)/%.c.o: %.c
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD_DIR)/%.c.o: $(BUILD_DIR)/%.c
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD_DIR)/%.interface.c $(BUILD_DIR)/%.interface.h: %.interface
	$(DO_MAKE_DIR)
	$(LAYER2_SCRIPT) --format avr_c --output-source $(basename $@).c --output-header $(basename $@).h --robonet-header $(ROBONET_PATH)/robonet.h $<

$(BUILD_DIR)/%.s.o: %.s
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD_DIR)/%.c.d: %.c
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) -MM -MG -MT $@ -MT $(@:.d=.o) -MF $@ $<

$(BUILD_DIR)/%.s.d: %.s
	$(DO_MAKE_DIR)
	$(CC) $(CFLAGS) -MM -MG -MT $@ -MT $(@:.d=.o) -MF $@ $<

$(BUILD_DIR)/%.interface.d: %.interface
	$(DO_MAKE_DIR)
	$(LAYER2_SCRIPT) --format avr_dependency --output $@ --target $@ --target $(@:.d=.o) $<

%.hex: %.elf
	$(OBJCOPY) -j .text -j .data -O ihex $< $@

.PHONY: upload
upload: $(GOAL_FILE)
	$(AVRDUDE_COMMAND) -U flash:w:$(GOAL_FILE):i

.PHONY: fuses
fuses:
	$(AVRDUDE_COMMAND) -U lfuse:w:0xe4:m -U hfuse:w:0xd8:m

.PHONY: objdump
objdump: $(GOAL_FILE:.hex=.elf)
	$(OBJDUMP) -S $< | less

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)

-include $(DEPFILES)
