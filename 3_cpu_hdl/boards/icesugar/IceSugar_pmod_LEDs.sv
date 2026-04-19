
module IceSugar_pmod_LEDs (
    input  logic [7:0] value,
    output logic [7:0] ICESUGAR_PMOD2_LED
);
  assign ICESUGAR_PMOD2_LED = ~value;
endmodule
