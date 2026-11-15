/* Two flash sectors, with only confirmed profiles written to storage. */
#pragma once
#include "hardware/flash.h"
#include "hardware/sync.h"

enum {
    RADIO_PROFILE_SLOT_COUNT = 2,
    RADIO_PROFILE_FLASH_OFFSET = PICO_FLASH_SIZE_BYTES - RADIO_PROFILE_SLOT_COUNT * FLASH_SECTOR_SIZE
};
_Static_assert(PICO_FLASH_SIZE_BYTES == 2048 * 1024, "Update the reserved flash region for this board");

static const uint32_t radio_profile_magic = 0x31504652u; /* RFP1 */
extern const uint8_t __flash_binary_end[];

static const uint8_t *radio_profile_slot(unsigned slot) {
    return (const uint8_t *)(XIP_BASE + RADIO_PROFILE_FLASH_OFFSET + slot * FLASH_SECTOR_SIZE);
}

static bool radio_profile_valid(unsigned profile) {
    return profile == RADIO_PROFILE_DBPSK_1200_V3 || profile == RADIO_PROFILE_DBPSK_DL1500_V3;
}

static int radio_profile_latest(void) {
    int latest = -1;
    for (unsigned slot = 0; slot < RADIO_PROFILE_SLOT_COUNT; ++slot) {
        const uint8_t *data = radio_profile_slot(slot);
        if (ul_u32(data) != radio_profile_magic || !radio_profile_valid(ul_u32(data + 8)) ||
            ul_u32(data + 12) != bp_crc32(data, 12))
            continue;
        if (latest < 0 ||
            (int32_t)(ul_u32(data + 4) - ul_u32(radio_profile_slot((unsigned)latest) + 4)) > 0)
            latest = (int)slot;
    }
    return latest;
}

static bool radio_profile_save(unsigned profile) {
    if (!radio_profile_valid(profile) ||
        (uintptr_t)__flash_binary_end > XIP_BASE + RADIO_PROFILE_FLASH_OFFSET)
        return false;
    int latest = radio_profile_latest();
    if (latest >= 0 && ul_u32(radio_profile_slot((unsigned)latest) + 8) == profile)
        return true;

    unsigned next = latest < 0 ? 0u : (unsigned)latest ^ 1u;
    uint32_t generation = latest < 0 ? 0u : ul_u32(radio_profile_slot((unsigned)latest) + 4) + 1u;
    uint8_t page[FLASH_PAGE_SIZE];
    memset(page, 0xff, sizeof(page));
    ul_p32(page, radio_profile_magic);
    ul_p32(page + 4, generation);
    ul_p32(page + 8, profile);
    ul_p32(page + 12, bp_crc32(page, 12));

    unsigned offset = RADIO_PROFILE_FLASH_OFFSET + next * FLASH_SECTOR_SIZE;
    /* Core 0 owns the transceiver. Keep interrupts out of XIP while flash is busy.
     * Preserve the current record until the other slot has been programmed. */
    uint32_t irq_state = save_and_disable_interrupts();
    flash_range_erase(offset, FLASH_SECTOR_SIZE);
    flash_range_program(offset, page, sizeof(page));
    restore_interrupts(irq_state);
    return memcmp(radio_profile_slot(next), page, sizeof(page)) == 0;
}
