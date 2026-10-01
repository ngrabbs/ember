package com.example.ember;

public final class WireChecks {
    public static int crc(byte[] bytes, int length) {
        int value = 0xffff;
        for (int i = 0; i < length; i++) {
            value ^= (bytes[i] & 0xff) << 8;
            for (int bit = 0; bit < 8; bit++) {
                value = ((value & 0x8000) != 0 ? (value << 1) ^ 0x1021 : value << 1) & 0xffff;
            }
        }
        return value;
    }
}
