/* Offline PBCH check using srsRAN 4G. Input: little-endian cf32 at 1.92 Msps. */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "srsran/srsran.h"
#include "srsran/phy/ue/ue_mib.h"

static int read_samples(void *opaque, cf_t *buffers[SRSRAN_MAX_CHANNELS],
                        uint32_t samples, srsran_timestamp_t *timestamp)
{
  (void)timestamp;
  if (fread(buffers[0], sizeof(cf_t), samples, (FILE *)opaque) != samples) {
    fprintf(stderr, "Input exhausted before MIB decode\n");
    exit(1);
  }
  return (int)samples;
}

int main(int argc, char **argv)
{
  if (argc != 3) {
    fprintf(stderr, "Usage: %s input-1m92.cf32 physical-cell-id\n", argv[0]);
    return 2;
  }
  char *end = NULL;
  long id = strtol(argv[2], &end, 10);
  if (*end || id < 0 || id > 503) return 2;
  FILE *input = fopen(argv[1], "rb");
  if (!input) { perror("input"); return 2; }
  alarm(10); /* Bound decoder work even if synchronization never advances. */
  srsran_ue_mib_sync_t sync = {0};
  srsran_cell_t cell = {0};
  cell.id = (uint32_t)id;
  cell.cp = SRSRAN_CP_NORM;
  cell.frame_type = SRSRAN_FDD;
  cell.nof_prb = 6;
  if (srsran_ue_mib_sync_init_multi(&sync, read_samples, 1, input)) return 2;
  if (srsran_ue_mib_sync_set_cell(&sync, cell)) return 2;
  uint8_t payload[SRSRAN_BCH_PAYLOAD_LEN] = {0};
  uint32_t ports = 0, sfn = 0;
  int offset = 0;
  int result = srsran_ue_mib_sync_decode(&sync, 40, payload, &ports, &offset);
  printf("PBCH decoder result: %d (1 means CRC-validated MIB)\n", result);
  if (result == SRSRAN_UE_MIB_FOUND) {
    srsran_pbch_mib_unpack(payload, &cell, &sfn);
    printf("PCI=%u PRB=%u ports=%u SFN=%u offset=%d\n",
           cell.id, cell.nof_prb, ports, sfn, offset);
    printf("MIB bits: ");
    for (unsigned i = 0; i < SRSRAN_BCH_PAYLOAD_LEN; ++i) printf("%u", payload[i]);
    puts("");
  }
  srsran_ue_mib_sync_free(&sync);
  fclose(input);
  return result == SRSRAN_UE_MIB_FOUND ? 0 : 1;
}
