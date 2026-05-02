
// TODO: test me
module flags
    import types::*;
(
    input logic clk,
    input logic reset,
    
    input flags_t flags_in,
    output flags_t flags_out,
    
    input logic ctrl_load_flags
);
    always_ff @(posedge clk) begin
        if (reset) begin
            flags_out <= '0;
        end else if (ctrl_load_flags) begin
            flags_out <= flags_in;
        end
    end
endmodule