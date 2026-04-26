import inspect
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb_tools.runner import get_runner

from test_utilities.clock import tick
from test_utilities.repo_root import repo_root


def setup_cocotb_tests(
    caller_globals,
    sources: list[Path] | None = None,
    hdl_toplevel: str | None = None,
    default_verilog_defines: dict[str, str] | None = None,
    auto_clk: bool = False,
    auto_reset: bool = False,
):
    if auto_reset and not auto_clk:
        raise ValueError("auto_reset requires auto_clk (synchronous reset needs a clock edge)")

    test_module = caller_globals["__name__"]  # e.g. "test_program_counter"
    module_file = Path(caller_globals["__file__"])

    types_sv = repo_root / "pkg3_cpu_hdl" / "types.sv"

    if sources is None:
        # default to loading all sources in the test directory
        sources = sorted(module_file.parent.glob("*.sv"))

    # types.sv must come first so packages are available to every module that imports them
    sources = [types_sv, *sources]

    if hdl_toplevel is None:
        # default to loading the module with the same name as the test file, minus the "test_" prefix
        hdl_toplevel = test_module.removeprefix("test_")

    test_functions = [
        (name, fn)
        for name, fn in sorted(caller_globals.items())
        if inspect.isfunction(fn) and fn.__module__ == test_module and name.startswith("test_")
    ]

    def make_wrappers(test_name: str, fn, default_verilog_defines):
        if default_verilog_defines is None:
            default_verilog_defines = {}

        defines = (
            {**default_verilog_defines, **fn._verilog_defines}
            if hasattr(fn, "_verilog_defines")
            else default_verilog_defines
        )

        # the code pytest will run (which then triggers cocotb to take over)
        def pytest_wrapper_fn():
            repo_root = Path(__file__).resolve().parents[1]
            build_dir = repo_root / "build" / "cocotb" / test_module

            runner = get_runner("icarus")
            runner.build(
                sources=sources,
                hdl_toplevel=hdl_toplevel,
                build_dir=str(build_dir),
                build_args=["-g2012", "-DCOCOTB_SIM=1"],
                timescale=("1ns", "1ps"),
                # TODO: support waves
                waves=False,
                # changing 'defines' does not trigger a re-compile, force a new build every time
                always=True,
                defines=defines,
            )
            runner.test(
                hdl_toplevel=hdl_toplevel,
                test_module=test_module,
                build_dir=str(build_dir),
                waves=False,
                # TODO: test filter is new, but not working
                testcase=f"cocotb_{test_name}",
                # test_filter=f"^cocotb_{test_name}$",
            )

        pytest_wrapper_fn.__name__ = test_name
        pytest_wrapper_fn.__qualname__ = test_name

        # the code cocotb will run
        @cocotb.test(name=f"cocotb_{test_name}")
        async def cocotb_wrapper_fn(dut):
            if auto_clk:
                # start the clock and do not block, allow it to run in the background
                cocotb.start_soon(Clock(dut.clk, 2, unit="ns").start())

            if auto_reset:
                dut.reset.value = 1
                await tick(dut)
                dut.reset.value = 0

            await fn(dut)

        cocotb_wrapper_fn.__qualname__ = f"cocotb_{test_name}"

        return pytest_wrapper_fn, cocotb_wrapper_fn

    for test_name, fn in test_functions:
        pytest_wrapper_fn, cocotb_wrapper_fn = make_wrappers(test_name, fn, default_verilog_defines)

        # the original test function, that cocotb will run after building
        # cocotb finds tests by walking module globals after import - expose it
        caller_globals[f"cocotb_{test_name}"] = cocotb_wrapper_fn

        # replace the original test_ function our wrapped version
        caller_globals[test_name] = pytest_wrapper_fn
