"""Run the actual Si5351 driver against a host-side I2C mock (requires cc)."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HEADER = """
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
typedef struct { int unused; } i2c_inst_t;
int i2c_write_blocking(i2c_inst_t *, uint8_t, const uint8_t *, size_t, bool);
int i2c_read_blocking(i2c_inst_t *, uint8_t, uint8_t *, size_t, bool);
"""
HARNESS = r"""
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include "si5351a.h"
#include "hardware/i2c.h"
static int reads, ready_at, writes, fail;
static uint8_t probe_status;
int i2c_write_blocking(i2c_inst_t *d, uint8_t a, const uint8_t *b,
                       size_t n, bool restart) {
    (void)d; (void)a; (void)b; (void)restart;
    if (fail) return -1;
    if (n > 1) ++writes;
    return (int)n;
}
int i2c_read_blocking(i2c_inst_t *d, uint8_t a, uint8_t *b,
                      size_t n, bool restart) {
    (void)d; (void)a; (void)restart;
    ++reads;
    *b = ready_at ? (reads < ready_at ? SI5351_STATUS_SYS_INIT : 0)
                  : probe_status;
    return (int)n;
}
static void reset(int ready) {
    reads = writes = fail = 0; ready_at = ready; probe_status = 0;
}
int main(void) {
    si5351_dev_t dev = {0}; si5351_status_t status;
    reset(1); assert(si5351_init(&dev) == 0); assert(reads == 1);
    reset(100); assert(si5351_init(&dev) == 0); assert(reads == 100);
    reset(101); assert(si5351_init(&dev) == -1);
    assert(reads == 100 && writes == 0);
    reset(0); fail = 1; assert(si5351_init(&dev) == -1);
    assert(reads == 0 && writes == 0);
    reset(0); assert(si5351_probe(&dev, &status) == 0);
    assert(status.present && status.raw_status == 0 && writes == 0);
    probe_status = SI5351_STATUS_LOL_A | SI5351_STATUS_LOL_B | 1;
    assert(si5351_probe(&dev, &status) == 0);
    assert(status.lol_a && status.lol_b && status.revid == 1 && writes == 0);
    fail = 1; assert(si5351_probe(&dev, &status) == -1);
    assert(!status.present && status.raw_status == 0);
    puts("PASS: initialization boundary, stuck/absent device, read-only probe");
}
"""

with tempfile.TemporaryDirectory(prefix="ember-si5351-test-") as directory:
    work = Path(directory)
    (work / "hardware").mkdir()
    (work / "hardware/i2c.h").write_text(HEADER)
    (work / "test.c").write_text(HARNESS)
    drivers = ROOT / "firmware/comms/drivers"
    subprocess.run([
        "cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
        f"-I{work}", f"-I{drivers}", str(work / "test.c"),
        str(drivers / "si5351a.c"), "-o", str(work / "test"),
    ], check=True)
    subprocess.run([str(work / "test")], check=True)
