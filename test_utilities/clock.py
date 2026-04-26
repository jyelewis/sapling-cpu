from cocotb.triggers import FallingEdge, RisingEdge, Timer


async def tick(dut):
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)


async def comb_tick():
    await Timer(1, unit="ns")
