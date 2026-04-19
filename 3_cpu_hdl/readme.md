# Sapling CPU: CPU HDL

Design and implementation of a simple CPU in System Verilog. The CPU is designed to be implemented on an FPGA, specifically targeting the iCE40 series.

## Required tools:
 - yosys: System Verilog synthesis
 - nextpnr-ice40: Place and route tool for iCE40 series
 - icepack: Tool for converting the .asc bitstream to ICE .bin bitstream format

# Commands:
 - `make build`: Compile the System Verilog code and generate the .bin FPGA bitstream
 - `make flash`: Flash the generated .bin FPGA bitstream to a connected iCE40 FPGA using
 - `make clean`: Clean up generated files and directories
 - `make test`: Run all cocotb tests
