
module top
  import IceSugar_HID_RGB_LED::*;
(
    input  logic ICESUGAR_CLK,
    output logic ICESUGAR_LED_R,
    output logic ICESUGAR_LED_G,
    output logic ICESUGAR_LED_B,

    output logic [7:0] ICESUGAR_PMOD2_LED
);

  logic generated_clk;
  logic clk;

  // iCESugar clock is 12 MHz - divide down to get a 1hz clock
  clock_divider #(
      .DIVISOR(12_000_000)
  ) clock_divider (
      .clk_in (ICESUGAR_CLK),
      .clk_out(generated_clk),
      .reset  (1'b0)
  );

  SB_GB u_gb_step (
      .USER_SIGNAL_TO_GLOBAL_BUFFER(generated_clk),
      .GLOBAL_BUFFER_OUTPUT        (clk)
  );

  sapling_cpu_core cpu (
      .clk(clk),
      .reset(1'b0),
      .memory_address(),
      .memory_read_data(16'h0000),
      .memory_write_data(),
      .memory_write_enable(),
      .memory_ready(1'b1)
  );

  color_t       color;
  logic   [7:0] tick_number;

  always_ff @(posedge clk) begin
    color <= color_t'(color + 1);  // wraps 000 -> 111 -> 000
    tick_number <= tick_number + 1;
  end

  IceSugar_HID_RGB_LED rgb_led (
      .RGB_color(color),
      .ICESUGAR_LED_R(ICESUGAR_LED_R),
      .ICESUGAR_LED_G(ICESUGAR_LED_G),
      .ICESUGAR_LED_B(ICESUGAR_LED_B)
  );

  IceSugar_pmod_LEDs pmod_leds (
      .ICESUGAR_PMOD2_LED(ICESUGAR_PMOD2_LED),
      .value(tick_number)
  );
endmodule
