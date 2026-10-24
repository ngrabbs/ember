# IHU Pico mode demo

Standalone **demo-only** 0.1.0 application for the original RP2040 Raspberry Pi
Pico/Pico H. Builds `ihu_demo.uf2`; the operational CAN Feather target remains
`firmware/ihu` / `ihu.uf2`. This target is intentionally separate so a teaching
image cannot silently replace the CAN/EPS application profile.

[Download the 0.1.0 UF2 hardware-test candidate](releases/0.1.0/README.md).

[Step-by-step install, wiring, console walkthrough and hardware acceptance](../../docs/user/ihu-pico-demo.md).

Uses the same pinned FreeRTOS 11.2.0 kernel and shared mode/output vocabulary as
the IHU candidate. A single statically allocated application task owns inputs,
mode transitions and USB console. SDK USB integration also uses the kernel timer
task. GPIO14/15 are pulled-up inputs; only the Pico LED is driven. No CAN, I2C,
UART, RF, actuator, external watchdog or nonvolatile-state backend is linked.
Health and commissioning checks are operator-controlled simulations. This is not
the full spacecraft state-machine specification or its acceptance implementation.

```sh
cmake -S firmware/ihu_demo -B build/ihu_demo \
  -DPICO_SDK_PATH="$PICO_SDK_PATH" -DPICO_BOARD=pico \
  $(python3 firmware/transceiver/source_identity.py --cmake-args)
cmake --build build/ihu_demo -j4
# build/ihu_demo/ihu_demo.uf2
```

Network access is needed on first configure to fetch the exact hashed kernel.
Use Pico SDK 2.1.1 and the ARM GNU toolchain used for the IHU candidate, or record
and retest any toolchain change. Board overrides other than `pico` are rejected.
The demo has its own VERSION and always identifies its role as IHU_DEMO.

Native model tests (Clang or GCC):

```sh
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
  firmware/ihu_demo/demo.c firmware/ihu_demo/tests/test_demo.c -o /tmp/ihu_demo_test
/tmp/ihu_demo_test
```

The model uses unsigned elapsed times, qualified independent input debouncing,
both-input release, 10/15-second demo waits from one release reference, explicit
checkout/approval and guarded fault recovery. Reclosure after release immediately
enters SAFE; only release is debounced. Tests cover staggered release, bounce,
timer boundaries/wrap, premature approval, both reinsertion paths, fault clearing
and reset without retained progress. See the installation guide for remaining
physical acceptance; passing native tests is not hardware validation.
