PYTHON      ?= uv run python
UV          ?= uv

ASSEMBLER   := $(PYTHON) pkg4_compiler/assembler.py
VM          := $(PYTHON) pkg5_vm/vm.py

BUILD_DIR   := build
SAM_DIRS    := pkg4_compiler pkg5_vm/programs pkg6_software
SAM_SRCS    := $(foreach d,$(SAM_DIRS),$(wildcard $(d)/*.sam))
BIN_OUTS    := $(patsubst %.sam,$(BUILD_DIR)/%.bin,$(SAM_SRCS))

# ---- HDL ----
HDL_DIR     := pkg3_cpu_hdl
BOARD       ?= icesugar
HDL_BUILD   := $(BUILD_DIR)/$(HDL_DIR)/$(BOARD)

BOARD_SRCS  := $(filter-out %_tb.sv, $(wildcard $(HDL_DIR)/boards/$(BOARD)/*.sv))
MODULE_SRCS := $(filter-out %_tb.sv, $(wildcard $(HDL_DIR)/modules/**/*.sv))
SV_SRCS     := $(BOARD_SRCS) $(MODULE_SRCS)

# Pull in per-board config (BOARD_CHIP, BOARD_PACKAGE, BOARD_FLASH_CMD, BOARD_PCF_NAME)
-include $(HDL_DIR)/boards/$(BOARD)/board.mk

BOARD_PCF   := $(HDL_DIR)/boards/$(BOARD)/$(BOARD_PCF_NAME)

# --- top-level aggregate targets ------------------------------------------

.PHONY: all
all: sam-all hdl-build

.PHONY: test
test:
	$(PYTHON) -m pytest

.PHONY: lint
lint:
	$(UV) run ruff check
	$(MAKE) hdl-lint

.PHONY: fmt
fmt:
	$(UV) run ruff check --fix
	$(UV) run ruff format
	$(MAKE) hdl-fmt

.PHONY: fmt-check
fmt-check:
	$(UV) run ruff format --check

.PHONY: check
check: lint test sam-all hdl-build

# --- .sam assembly / running ----------------------------------------------

.PHONY: sam-all
sam-all: $(BIN_OUTS)

# Assemble every .sam file under the known source directories into build/
$(BUILD_DIR)/%.bin: %.sam
	@mkdir -p $(dir $@)
	$(ASSEMBLER) $< -o $@

# Run a .bin in the VM: `make run-bin BIN=build/pkg6_software/hello.bin`
.PHONY: run-bin
run-bin:
ifndef BIN
	$(error set BIN=path/to/program.bin (e.g. make run-bin BIN=build/pkg6_software/hello.bin))
endif
	$(VM) $(BIN)

# Compile a .sam and run it in the VM: `make run-sam SAM=pkg6_software/hello.sam`
.PHONY: run-sam
run-sam:
ifndef SAM
	$(error set SAM=path/to/program.sam (e.g. make run-sam SAM=pkg6_software/hello.sam))
endif
	@mkdir -p $(dir $(BUILD_DIR)/$(SAM:.sam=.bin))
	$(ASSEMBLER) $(SAM) -o $(BUILD_DIR)/$(SAM:.sam=.bin)
	$(VM) $(BUILD_DIR)/$(SAM:.sam=.bin)

# --- HDL (System Verilog) -------------------------------------------------

.PHONY: hdl-build
hdl-build: $(HDL_BUILD)/top.bin

.PHONY: hdl-flash
hdl-flash: $(HDL_BUILD)/top.bin
	$(BOARD_FLASH_CMD)

.PHONY: hdl-files
hdl-files:
	@echo $(SV_SRCS) | tr ' ' '\n'

.PHONY: hdl-fmt
hdl-fmt:
	verible-verilog-format --inplace $(SV_SRCS)

.PHONY: hdl-lint
hdl-lint:
	verible-verilog-lint $(SV_SRCS)

$(HDL_BUILD):
	mkdir -p $@

$(HDL_BUILD)/top.json: $(SV_SRCS) | $(HDL_BUILD)
	yosys -p "plugin -i slang; read_slang $(SV_SRCS); synth_ice40 -top top -json $@"

$(HDL_BUILD)/top.asc: $(HDL_BUILD)/top.json $(BOARD_PCF)
	nextpnr-ice40 --$(BOARD_CHIP) --package $(BOARD_PACKAGE) --json $< --pcf $(BOARD_PCF) --asc $@

$(HDL_BUILD)/top.bin: $(HDL_BUILD)/top.asc
	icepack $< $@

# --- misc -----------------------------------------------------------------

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

.PHONY: help
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
