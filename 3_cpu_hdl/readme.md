# Sapling CPU: CPU HDL

Design and implementation of a simple CPU in System Verilog. The CPU is designed to be implemented on an FPGA, specifically targeting the iCE40 series.

## Required tools:
 - yosys: System Verilog synthesis
 - slang: yosys plugin for modern system verilog features
 - nextpnr-ice40: Place and route tool for iCE40 series
 - icepack: Tool for converting the .asc bitstream to ICE .bin bitstream format
 - verible: System Verilog linting and formatting

All commands live in the root `Makefile`. HDL-specific targets are prefixed with `hdl-`:

 - `make hdl-build` — synthesize + place+route + pack the FPGA bitstream
 - `make hdl-flash` — flash the bitstream to a connected iCE40 FPGA
 - `make hdl-files` — list .sv files included in the build
 - `make hdl-fmt`   — format .sv sources with verible
 - `make hdl-lint`  — lint .sv sources with verible
 - `make test`      — run all pytest suites (includes cocotb)
 - `make check`     — lint + test + hdl-build
