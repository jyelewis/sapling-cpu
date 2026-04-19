DEVICE_TOP_FILE = top_ice
DEVICE_PCF = icesugar.pcf
DEVICE_CHIP = up5k
DEVICE_PACKAGE = sg48

SV_SRCS = $(DEVICE_TOP_FILE).sv

# ------------------------------------------

all: $(DEVICE_TOP_FILE).bin

clean:
	rm -f $(DEVICE_TOP_FILE).json $(DEVICE_TOP_FILE).asc $(DEVICE_TOP_FILE).bin

flash: $(DEVICE_TOP_FILE).bin
	icesprog -w $<

# ------------------------------------------

$(DEVICE_TOP_FILE).json: $(SV_SRCS)
	yosys -p "synth_ice40 -top top -json $@" $(SV_SRCS)
	
$(DEVICE_TOP_FILE).asc: $(DEVICE_TOP_FILE).json $(DEVICE_PCF)
	nextpnr-ice40 --$(DEVICE_CHIP) --package $(DEVICE_PACKAGE) --json $(DEVICE_TOP_FILE).json --pcf $(DEVICE_PCF) --asc $@

$(DEVICE_TOP_FILE).bin: $(DEVICE_TOP_FILE).asc
	icepack $< $@


.PHONY: all clean
