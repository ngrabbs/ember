#pragma once
static uint8_t packet_frame[BPSK_FRAME_SIZE];
/* Absolute symbol deadlines, IRQs enabled. Abort if a symbol is >150us late. */
static bool bpsk_emit(uint64_t deadline) {
    uint64_t start=time_us_64();
    bool phase=false;
    for(unsigned bit=0;bit<BPSK_FRAME_SIZE*8u;bit++) {
        uint64_t due=start+(uint64_t)bit*1000000/BPSK_BAUD;
        while(time_us_64()<due)
            if(clock_deadline_fired || getchar_timeout_us(0)>=0)return false;
        uint64_t now=time_us_64();
        if(now>=deadline || now>due+150 || clock_deadline_fired ||
           getchar_timeout_us(0)>=0)return false;
        phase ^= (packet_frame[bit/8]>>(7-bit%8))&1;
        gpio_put(16,phase);
    }
    uint64_t end=start+(uint64_t)BPSK_FRAME_SIZE*8u*1000000/BPSK_BAUD;
    while(time_us_64()<end)
        if(clock_deadline_fired || getchar_timeout_us(0)>=0)return false;
    return time_us_64()<deadline && !clock_deadline_fired;
}
