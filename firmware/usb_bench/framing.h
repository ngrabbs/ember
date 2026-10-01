#pragma once
#include <stddef.h>
#include <stdint.h>
size_t cobs_encode(const uint8_t *, size_t, uint8_t *, size_t);
size_t cobs_decode(const uint8_t *, size_t, uint8_t *, size_t);
