#pragma once
static uint8_t packet_frame[BPSK_FRAME_MAX];
static size_t packet_frame_size=BPSK_FRAME_SIZE;
/* Absolute symbol deadlines, IRQs enabled. Abort if a symbol is >150us late. */
static bool bpsk_emit(uint64_t deadline) {
    if(!packet_frame_size || packet_frame_size>BPSK_FRAME_MAX)return false;
    uint64_t start=time_us_64();
    bool phase=false;
    for(unsigned bit=0;bit<packet_frame_size*8u;bit++) {
        uint64_t due=start+(uint64_t)bit*1000000/BPSK_BAUD;
        while(time_us_64()<due)
            if(clock_deadline_fired || getchar_timeout_us(0)>=0)return false;
        uint64_t now=time_us_64();
        if(now>=deadline || now>due+150 || clock_deadline_fired ||
           getchar_timeout_us(0)>=0)return false;
        phase ^= (packet_frame[bit/8]>>(7-bit%8))&1;
        gpio_put(16,phase);
    }
    uint64_t end=start+(uint64_t)packet_frame_size*8u*1000000/BPSK_BAUD;
    while(time_us_64()<end)
        if(clock_deadline_fired || getchar_timeout_us(0)>=0)return false;
    return time_us_64()<deadline && !clock_deadline_fired;
}

/* Ten alternating 100ms holds: one second total, existing 2s mute timer. */
static bool phase_hold_emit(uint64_t deadline) {
    uint64_t start=time_us_64();
    for(unsigned state=0;state<10;state++) {
        uint64_t due=start+(uint64_t)state*100000;
        while(time_us_64()<due)
            if(clock_deadline_fired || getchar_timeout_us(0)>=0)return false;
        uint64_t now=time_us_64();
        if(now>=deadline || now>due+150 || clock_deadline_fired ||
           getchar_timeout_us(0)>=0)return false;
        gpio_put(16,state&1u);
    }
    while(time_us_64()<start+1000000)
        if(time_us_64()>=deadline || clock_deadline_fired ||
           getchar_timeout_us(0)>=0)return false;
    return time_us_64()<deadline && !clock_deadline_fired;
}
