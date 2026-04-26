import inspect
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb_tools.runner import get_runner


def setup_cocotb_tests(
    caller_globals,
    sources: list[Path] | None = None,
    hdl_toplevel: str | None = None,
    auto_clk: bool = False,
    auto_reset: bool = False,
):
    test_module = caller_globals["__name__"]  # "test_program_counter"
    module_file = Path(caller_globals["__file__"])

    if sources is None:
        sources = list(module_file.parent.glob("*.sv"))

    if hdl_toplevel is None:
        hdl_toplevel = test_module.removeprefix("test_")

    test_functions = [
        (name, fn)
        for name, fn in caller_globals.items()
        if inspect.isfunction(fn) and fn.__module__ == test_module and name.startswith("test_")
    ]

    def make_wrappers(test_name: str, fn):
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
                waves=False,
            )
            runner.test(
                hdl_toplevel=hdl_toplevel,
                test_module=test_module,
                build_dir=str(build_dir),
                waves=False,
                testcase=f"cocotb_{test_name}",
            )

        # the code cocotb will run
        @cocotb.test(name=f"cocotb_{test_name}")
        async def cocotb_wrapper_fn(dut):
            from cocotb.triggers import Timer

            if auto_clk:
                # start the clock and do not block, allow it to run in the background
                cocotb.start_soon(Clock(dut.clk, 2, unit="ns").start())

            if auto_reset:
                if auto_clk:
                    # tick the clock when we reset
                    dut.reset.value = 1
                    await tick(dut)
                    dut.reset.value = 0
                else:
                    # no clock, pulse reset instead
                    dut.reset.value = 1
                    await Timer(1, unit="ns")
                    dut.reset.value = 0

            await fn(dut)

        return pytest_wrapper_fn, cocotb_wrapper_fn

    for test_name, fn in test_functions:
        pytest_wrapper_fn, cocotb_wrapper_fn = make_wrappers(test_name, fn)

        # the original test function, that cocotb will run after building
        caller_globals[f"cocotb_{test_name}"] = cocotb_wrapper_fn

        # the pytest function, which builds & configures before calling cocotb to execute
        caller_globals[test_name] = pytest_wrapper_fn


async def tick(dut):
    from cocotb.triggers import FallingEdge, RisingEdge

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
