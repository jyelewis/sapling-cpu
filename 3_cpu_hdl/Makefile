BOARD ?= icesugar

# Pull in per-board config (CHIP, PACKAGE, PCF, FLASH_CMD)
include boards/$(BOARD)/board.mk

BOARD_SRCS = $(filter-out %_tb.sv, $(wildcard boards/$(BOARD)/*.sv))
MODULE_SRCS = $(filter-out %_tb.sv, $(wildcard modules/*.sv))

SV_SRCS = $(BOARD_SRCS) $(MODULE_SRCS)

# ------------------------------------------

BUILD = build/$(BOARD)
PROJ  = $(BUILD)/top

build: $(PROJ).bin

flash: $(PROJ).bin
	$(BOARD_FLASH_CMD) $

files:
	@echo $(SV_SRCS) | tr ' ' '\n'

fmt:
	verible-verilog-format --inplace $(SV_SRCS)

lint:
	verible-verilog-lint $(SV_SRCS)

clean:
	rm -rf build/

check: fmt lint build
# ------------------------------------------

$(BUILD):
	mkdir -p $@

$(PROJ).json: $(SV_SRCS) | $(BUILD)
	yosys -p "plugin -i slang; read_slang $(SV_SRCS); synth_ice40 -top top -json $@"

$(PROJ).asc: $(PROJ).json $(BOARD_PCF)
	nextpnr-ice40 --$(BOARD_CHIP) --package $(BOARD_PACKAGE) --json $< --pcf $(BOARD_PCF) --asc $@

$(PROJ).bin: $(PROJ).asc
	icepack $< $@


.PHONY: all flash files fmt lint clean
