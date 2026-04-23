
package IceSugar_HID_RGB_LED;
  typedef enum logic [2:0] {
    COLOR_OFF     = 3'b000,
    COLOR_RED     = 3'b001,
    COLOR_GREEN   = 3'b010,
    COLOR_YELLOW  = 3'b011,
    COLOR_BLUE    = 3'b100,
    COLOR_MAGENTA = 3'b101,
    COLOR_CYAN    = 3'b110,
    COLOR_WHITE   = 3'b111
  } color_t;
endpackage

module IceSugar_HID_RGB_LED
  import IceSugar_HID_RGB_LED::*;
(
    input color_t RGB_color,

    output logic ICESUGAR_LED_G,
    output logic ICESUGAR_LED_R,
    output logic ICESUGAR_LED_B
);
  assign ICESUGAR_LED_R = ~RGB_color[0];
  assign ICESUGAR_LED_G = ~RGB_color[1];
  assign ICESUGAR_LED_B = ~RGB_color[2];
endmodule
