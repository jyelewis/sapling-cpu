
module top
  import IceSugar_HID_RGB_LED::*;
(
    input  logic ICESUGAR_CLK,
    output logic ICESUGAR_LED_R,
    output logic ICESUGAR_LED_G,
    output logic ICESUGAR_LED_B
);
  // iCESugar clock is 12 MHz — divide to ~2 Hz (half a second per colour)
  localparam int TickMax = 12_000_000 / 2;

  logic   [$clog2(TickMax)-1:0] tick;
  color_t                       color;

  always_ff @(posedge ICESUGAR_CLK) begin
    if (tick == TickMax - 1) begin
      tick  <= '0;
      color <= color_t'(color + 1);  // wraps 000 -> 111 -> 000
    end else begin
      tick <= tick + 1;
    end
  end

  IceSugar_HID_RGB_LED led_inst (
      .RGB_color(color),
      .ICESUGAR_LED_R(ICESUGAR_LED_R),
      .ICESUGAR_LED_G(ICESUGAR_LED_G),
      .ICESUGAR_LED_B(ICESUGAR_LED_B)
  );
endmodule
