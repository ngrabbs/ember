# Shared Pico CAN build support

The independent `ihu` and `walter_mcu` projects use this CAN Feather board
profile and SDK build configuration. `configure.cmake` reads the calling
application's own VERSION file, validates explicit source SHA/dirty inputs,
and generates its build identity and dictionary header. Runtime application
sources remain in their respective directories; neither builds the other.

`boards/ember_can_feather.h` preserves the existing RP2040/MCP25625 pin profile.
The original-Pico transceiver uses its own board/build configuration.
