#ifndef Y24_HELLO_H
#define Y24_HELLO_H
#include "can_fragment.h"
/* Accept only one complete, CRC-verified HELLO. No application commands. */
static inline size_t hello_response(const cf_reader *fragments, uint32_t boot,
                                   uint8_t *wire, uint32_t *request) {
    ul_reader reader = {0}; ul_packet in = {0}, out;
    unsigned packets = 0;
    for (size_t i = 0; i < fragments->used; ++i)
        if (ul_feed(&reader, fragments->wire[i], 0, &in)) ++packets;
    if (packets != 1 || reader.used || reader.discard || reader.crc_errors ||
        reader.framing_errors || reader.format_errors || reader.overflows ||
        in.version != UL_VERSION || in.type != UL_HELLO || in.size ||
        in.sender != in.origin || (uint16_t)in.request != fragments->token) return 0;
    ul_reply(&in, boot, &out);
    *request = in.request;
    return ul_encode(&out, wire);
}
#endif
