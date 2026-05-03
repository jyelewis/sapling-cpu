
// mostly works, suspect vastly overcomplicated
// TODO: re-write me
// TODO: test me

module sapling_test_board_controller (
    // TODO: whats the fastest we can safely drive the chips?
    // TODO: Syncing clock cycles? How can we be sure values are stable? What about reset?
    // we need their clock to reset & latch data in
    // is this our job or the thing above us?
    // TODO: think about clock syncing
    input logic clk,
    input logic reset,
    // TODO: is this a good name?
    input logic update_display,

    input logic [7:0] green_hex,
    input logic [7:0] red_hex,
    input logic [7:0] leds,

    output logic pin_spi_clk,
    output logic pin_spi_data,
    output logic pin_led_latch
);
  // TODO: decode the hex values
  //  logic has_pending_data;
  //  logic [4:0] bits_sent;
  //  logic [24:0] pending_pattern;
  typedef enum logic [1:0] {
    IDLE,
    SETUP,
    HOLD,
    LATCH
  } state_t;
  state_t state;
  logic [4:0] bits_sent;
  logic [23:0] pending_pattern;  // 24 bits, not 25

  always_ff @(posedge clk) begin
    pin_led_latch <= 0;
    pin_spi_clk   <= 0;

    if (reset) begin
      // TODO: reset should clear the display
      state     <= IDLE;
      bits_sent <= 0;
    end else begin
      unique case (state)
        IDLE:
        if (update_display) begin
          pending_pattern <= {leds, red_hex, green_hex};
          bits_sent       <= 0;
          state           <= SETUP;
        end

        SETUP: begin  // SCK low, present data
          pin_spi_data <= pending_pattern[23];
          pin_spi_clk  <= 0;
          state        <= HOLD;
        end

        HOLD: begin  // SCK high, 595 samples
          pin_spi_clk     <= 1;
          pending_pattern <= pending_pattern << 1;
          bits_sent       <= bits_sent + 1;
          state           <= (bits_sent == 23) ? LATCH : SETUP;
        end

        LATCH: begin
          pin_led_latch <= 1;
          state         <= IDLE;
        end
      endcase
    end
  end
endmodule
