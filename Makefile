PYTHON      ?= uv run python
UV          ?= uv

ASSEMBLER   := $(PYTHON) 4_compiler/assembler.py
VM          := $(PYTHON) 5_vm/vm.py

BUILD_DIR   := build
SAM_DIRS    := 4_compiler 5_vm/programs 6_software
SAM_SRCS    := $(foreach d,$(SAM_DIRS),$(wildcard $(d)/*.sam))
BIN_OUTS    := $(patsubst %.sam,$(BUILD_DIR)/%.bin,$(SAM_SRCS))

# ---- HDL ----
HDL_DIR     := 3_cpu_hdl
BOARD       ?= icesugar
HDL_BUILD   := $(BUILD_DIR)/$(HDL_DIR)/$(BOARD)

BOARD_SRCS  := $(filter-out %_tb.sv, $(wildcard $(HDL_DIR)/boards/$(BOARD)/*.sv))
MODULE_SRCS := $(filter-out %_tb.sv, $(wildcard $(HDL_DIR)/modules/*.sv))
SV_SRCS     := $(BOARD_SRCS) $(MODULE_SRCS)

# Pull in per-board config (BOARD_CHIP, BOARD_PACKAGE, BOARD_FLASH_CMD, BOARD_PCF_NAME)
-include $(HDL_DIR)/boards/$(BOARD)/board.mk

BOARD_PCF   := $(HDL_DIR)/boards/$(BOARD)/$(BOARD_PCF_NAME)

.PHONY: all test lint fmt fmt-check check \
        hdl-build hdl-flash hdl-files hdl-fmt hdl-lint hdl-test \
        sam-all run-bin run-sam clean help

# --- top-level aggregate targets ------------------------------------------

all: sam-all hdl-build

test:
	$(PYTHON) -m pytest

lint:
	$(UV) run ruff check
	$(MAKE) hdl-lint

fmt:
	$(UV) run ruff check --fix
	$(UV) run ruff format
	$(MAKE) hdl-fmt

fmt-check:
	$(UV) run ruff format --check

check: lint test hdl-build

# --- .sam assembly / running ----------------------------------------------

sam-all: $(BIN_OUTS)

# Assemble every .sam file under the known source directories into build/
$(BUILD_DIR)/%.bin: %.sam
	@mkdir -p $(dir $@)
	$(ASSEMBLER) $< -o $@

# Run a .bin in the VM: `make run-bin BIN=build/6_software/hello.bin`
run-bin:
ifndef BIN
	$(error set BIN=path/to/program.bin (e.g. make run-bin BIN=build/6_software/hello.bin))
endif
	$(VM) $(BIN)

# Compile a .sam and run it in the VM: `make run-sam SAM=6_software/hello.sam`
run-sam:
ifndef SAM
	$(error set SAM=path/to/program.sam (e.g. make run-sam SAM=6_software/hello.sam))
endif
	@mkdir -p $(dir $(BUILD_DIR)/$(SAM:.sam=.bin))
	$(ASSEMBLER) $(SAM) -o $(BUILD_DIR)/$(SAM:.sam=.bin)
	$(VM) $(BUILD_DIR)/$(SAM:.sam=.bin)

# --- HDL (System Verilog) -------------------------------------------------

hdl-build: $(HDL_BUILD)/top.bin

hdl-flash: $(HDL_BUILD)/top.bin
	$(BOARD_FLASH_CMD)

hdl-files:
	@echo $(SV_SRCS) | tr ' ' '\n'

hdl-fmt:
	verible-verilog-format --inplace $(SV_SRCS)

hdl-lint:
	verible-verilog-lint $(SV_SRCS)

hdl-test: test

$(HDL_BUILD):
	mkdir -p $@

$(HDL_BUILD)/top.json: $(SV_SRCS) | $(HDL_BUILD)
	yosys -p "plugin -i slang; read_slang $(SV_SRCS); synth_ice40 -top top -json $@"

$(HDL_BUILD)/top.asc: $(HDL_BUILD)/top.json $(BOARD_PCF)
	nextpnr-ice40 --$(BOARD_CHIP) --package $(BOARD_PACKAGE) --json $< --pcf $(BOARD_PCF) --asc $@

$(HDL_BUILD)/top.bin: $(HDL_BUILD)/top.asc
	icepack $< $@

# --- misc -----------------------------------------------------------------

clean:
	rm -rf $(BUILD_DIR)
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

help:
	@echo "Top-level targets:"
	@echo "  all             Assemble .sam files and build HDL bitstream"
	@echo "  test            Run all pytest suites (assembler, vm, cocotb)"
	@echo "  lint            Run ruff + HDL lint"
	@echo "  fmt             Auto-format python + HDL sources"
	@echo "  check           lint + test + hdl-build"
	@echo "  clean           Remove build/ and __pycache__"
	@echo ""
	@echo "Software targets:"
	@echo "  sam-all         Assemble every .sam file to build/"
	@echo "  run-bin BIN=..  Run a compiled .bin in the VM"
	@echo "  run-sam SAM=..  Compile a .sam and run it in the VM"
	@echo ""
	@echo "HDL targets:"
	@echo "  hdl-build       Synthesize + place+route + pack for BOARD=$(BOARD)"
	@echo "  hdl-flash       Flash the bitstream to the attached board"
	@echo "  hdl-files       List .sv files that will be included in the build"
	@echo "  hdl-fmt         Format .sv sources with verible"
	@echo "  hdl-lint        Lint  .sv sources with verible"
