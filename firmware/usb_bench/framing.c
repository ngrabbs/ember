#include "framing.h"
size_t cobs_encode(const uint8_t *input, size_t n, uint8_t *out, size_t capacity) {
    if (!n || n>240 || capacity<n+2) return 0;
    size_t code_at=0, next=1; uint8_t code=1;
    for (size_t i=0;i<n;i++) {
        if (!input[i]) { out[code_at]=code; code_at=next++; code=1; }
        else { out[next++]=input[i]; code++; }
    }
    out[code_at]=code; out[next++]=0; return next;
}
size_t cobs_decode(const uint8_t *input, size_t n, uint8_t *out, size_t capacity) {
    if (!n || n>241) return 0;
    size_t i=0, next=0;
    while (i<n) {
        uint8_t code=input[i++];
        if (!code || code==255 || i+(size_t)code-1>n) return 0;
        for (unsigned j=1;j<code;j++) {
            if (!input[i] || next>=capacity) return 0;
            out[next++]=input[i++];
        }
        if (i<n) { if (next>=capacity) return 0; out[next++]=0; }
    }
    return next;
}
