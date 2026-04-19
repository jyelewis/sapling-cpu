
module top (
    input  wire        ICESUGAR_CLK,
    output wire [7:0]  ICESUGAR_PMOD2_LED,
    output wire ICESUGAR_LED_G,
    output wire ICESUGAR_LED_R,
    output wire ICESUGAR_LED_B,
);
    logic [25:0] counter = 0;

    always_ff @(posedge ICESUGAR_CLK) begin
        counter <= counter + 1;
    end

    assign ICESUGAR_PMOD2_LED = ~counter[25:18];

    assign ICESUGAR_LED_G = 1;
    assign ICESUGAR_LED_R = 0;
    assign ICESUGAR_LED_B = 1;
endmodule
