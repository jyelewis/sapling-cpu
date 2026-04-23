PYTHON      ?= python3
ASSEMBLER   := $(PYTHON) 4_compiler/assembler.py
VM          := $(PYTHON) 5_vm/vm.py

BUILD_DIR   := build
SAM_DIRS    := 4_compiler 5_vm/programs 6_software
SAM_SRCS    := $(foreach d,$(SAM_DIRS),$(wildcard $(d)/*.sam))
BIN_OUTS    := $(patsubst %.sam,$(BUILD_DIR)/%.bin,$(SAM_SRCS))

.PHONY: all test test-vm test-assembler asm run run-sam clean help

all: $(BIN_OUTS)

# Assemble every .sam file under the known source directories into build/
$(BUILD_DIR)/%.bin: %.sam
	@mkdir -p $(dir $@)
	$(ASSEMBLER) $< -o $@

# Run a .bin in the VM: `make run BIN=build/5_vm/programs/io_echo.bin`
run-bin:
ifndef BIN
	$(error set BIN=path/to/program.bin (e.g. make run BIN=build/5_vm/programs/io_echo.bin))
endif
	$(VM) $(BIN)

# Compile a .sam and run it in the VM: `make run-sam SAM=5_vm/programs/hello.sam`
run-sam:
ifndef SAM
	$(error set SAM=path/to/program.sam (e.g. make run-sam SAM=5_vm/programs/hello.sam))
endif
	@mkdir -p $(dir $(BUILD_DIR)/$(SAM:.sam=.bin))
	$(ASSEMBLER) $(SAM) -o $(BUILD_DIR)/$(SAM:.sam=.bin)
	$(VM) $(BUILD_DIR)/$(SAM:.sam=.bin)

test:
	$(PYTHON) -m pytest

clean:
	rm -rf $(BUILD_DIR)
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

help:
	@echo "Targets:"
	@echo "  all            Assemble every .sam file to $(BUILD_DIR)/"
	@echo "  test           Run assembler and VM test suites"
	@echo "  test-assembler Run 4_compiler tests"
	@echo "  test-vm        Run 5_vm tests"
	@echo "  run-bin BIN=.. Run a compiled .bin in the VM"
	@echo "  run-sam SAM=.. Compile a .sam and run it in the VM"
	@echo "  clean          Remove $(BUILD_DIR)/ and __pycache__ dirs"
