# Shared EMBER command engine

Portable, HAL-free C command/result handling extracted from the retired USB
Pico application. `protocol.c` and `protocol.h` are unchanged by the move.
Wire offsets are generated into `wire.h` from
[`ground/ember/dictionary.json`](../../../ground/ember/dictionary.json).

The active IHU compiles this engine and uses it for the diagnostic native RF
PING route. IHU's RF allowlist and admission gates remain in
[`firmware/ihu/main.c`](../../ihu/main.c); extracting the generic engine does not
enable its other command handlers or periodic telemetry on a live interface.
Payload fire-check handling remains separate.

[`tests/ground/test_firmware.py`](../../../tests/ground/test_firmware.py) compiles
the engine with a host C compiler, then checks generated replies and transaction
caching with the independent Python codec. IHU parser/route tests also link it.
The old standalone USB `main.c`, CMake application and USB-only C framing are
removed; Python framing tests remain with the ground tools.
