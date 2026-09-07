// ---------------------------------------------------------------------------
// ad9910_ctrl - bring the AD9910 up and load two BPSK profiles
//
// EMBER experimental S-band payload, M1.
//
// Sequence:
//   1. pulse MASTER_RESET (active high) for a known starting state
//   2. write CFR3 to configure the REFCLK PLL, then pulse IO_UPDATE
//   3. wait for PLL_LOCK, with a timeout rather than a hang
//   4. write single-tone profile 0 (phase 0) and profile 1 (phase 180)
//   5. pulse IO_UPDATE
//
// After that the PROFILE pins select the phase, so BPSK costs one FPGA pin:
// drive PF0 from the symbol engine's tx_symbol and the carrier flips 180
// degrees per symbol. PF1/PF2 stay low.
//
// Nothing an AD9910 register says takes effect until IO_UPDATE is pulsed -
// writes land in a buffer. Forgetting that pulse is the classic way to spend
// an afternoon watching a part that appears not to respond to SPI at all.
//
// CFR3 for a 40 MHz reference and a 1 GHz system clock, from the Rev. B
// datasheet Table 20, with the VCO band from Table 8:
//
//   [26:24] VCO SEL = 101   VCO5, 920-1030 MHz, contains 1000
//   [21:19] Icp     = 111   387 uA, the default
//   [15]    REFCLK input divider BYPASSED, so the phase detector sees the
//           full 40 MHz rather than 20 - lower N and better phase noise
//   [14]    input divider ResetB = normal
//   [8]     PLL enable
//   [7:1]   N = 25          40 MHz x 25 = 1000 MHz, and 25 is inside the
//                           datasheet's 12x to 127x range
//
//   -> CFR3 = 0x0538C132
//
// The part powers up with VCO SEL = 111, which means PLL BYPASSED, so before
// this runs SYSCLK is just the 40 MHz reference. That is a useful fallback: a
// tone still appears without any PLL configuration, at 1/25 of the frequency.
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module ad9910_ctrl #(
    parameter int unsigned CLOCK_HZ    = 125_000_000,
    parameter int unsigned RESET_NS    = 10_000,        // MASTER_RESET width
    parameter int unsigned SETTLE_NS   = 10_000,        // after reset release
    parameter int unsigned IOUP_NS     = 100,           // IO_UPDATE width
    parameter int unsigned LOCK_TMO_US = 10_000         // PLL lock timeout
) (
    input  wire        clk,
    input  wire        rst,
    input  wire        start,          // pulse to run the sequence

    input  wire [31:0] ftw,            // frequency tuning word
    input  wire [15:0] pow0,           // profile 0 phase offset word
    input  wire [15:0] pow1,           // profile 1 phase offset word, 0x8000 = 180 deg
    input  wire [13:0] asf,            // amplitude scale factor, 0x3FFF = full
    input  wire [31:0] cfr3,           // PLL configuration; see the note above

    input  wire        pll_lock,       // AD9910 PLL_LOCK pin

    output logic       master_reset,   // AD9910 MASTER_RESET, active high
    output logic       io_update,      // AD9910 IO_UPDATE
    output logic       cs_n,           // AD9910 CSB

    output logic [7:0] spi_tx_data,
    output logic       spi_tx_valid,
    input  wire        spi_tx_ready,
    input  wire        spi_busy,      // needed to know the LAST byte has shifted

    output logic       busy,
    output logic       done,
    output logic       lock_timeout
);
    localparam int unsigned RESET_CYCLES  = (CLOCK_HZ / 1_000_000) * RESET_NS  / 1000;
    localparam int unsigned SETTLE_CYCLES = (CLOCK_HZ / 1_000_000) * SETTLE_NS / 1000;
    localparam int unsigned IOUP_CYCLES   = (CLOCK_HZ / 1_000_000) * IOUP_NS   / 1000;
    localparam int unsigned LOCK_CYCLES   = (CLOCK_HZ / 1_000_000) * LOCK_TMO_US;

    // AD9910 serial addresses
    localparam logic [7:0] ADDR_CFR3 = 8'h02;
    localparam logic [7:0] ADDR_PRF0 = 8'h0E;
    localparam logic [7:0] ADDR_PRF1 = 8'h0F;

    typedef enum logic [3:0] {
        S_IDLE, S_RST, S_SETTLE, S_CFR3, S_IOUP1, S_LOCK,
        S_PRF0, S_PRF1, S_IOUP2, S_DONE
    } state_e;
    state_e state;

    logic [31:0] timer;
    logic [71:0] shifter;        // up to 9 bytes: instruction + 8 data
    logic [3:0]  bytes_left;
    logic        launch;         // one-shot: load the shifter for this state

    // A single-tone profile is 64 bits: [61:48] ASF, [47:32] POW, [31:0] FTW.
    function automatic logic [63:0] profile(input logic [15:0] p);
        return {2'b00, asf, p, ftw};
    endfunction

    assign busy = (state != S_IDLE) && (state != S_DONE);
    assign done = (state == S_DONE);

    always_ff @(posedge clk) begin
        spi_tx_valid <= 1'b0;

        if (rst) begin
            state        <= S_IDLE;
            timer        <= '0;
            cs_n         <= 1'b1;
            master_reset <= 1'b0;
            io_update    <= 1'b0;
            lock_timeout <= 1'b0;
            bytes_left   <= '0;
            launch       <= 1'b0;
        end else begin
            case (state)
                // S_DONE handles start identically to S_IDLE. Routing S_DONE
                // through S_IDLE instead loses the pulse: start is one cycle
                // wide, so by the time the FSM reached S_IDLE it was gone and
                // the sequence never re-ran - every second 'i' did nothing.
                S_IDLE, S_DONE: if (start) begin
                    lock_timeout <= 1'b0;
                    master_reset <= 1'b1;
                    timer        <= '0;
                    state        <= S_RST;
                end

                S_RST: if (timer == RESET_CYCLES-1) begin
                    master_reset <= 1'b0;
                    timer        <= '0;
                    state        <= S_SETTLE;
                end else timer <= timer + 1'b1;

                S_SETTLE: if (timer == SETTLE_CYCLES-1) begin
                    timer      <= '0;
                    shifter    <= {ADDR_CFR3, cfr3, 32'b0};
                    bytes_left <= 4'd5;
                    cs_n       <= 1'b0;
                    launch     <= 1'b1;
                    state      <= S_CFR3;
                end else timer <= timer + 1'b1;

                // Shift the loaded transaction out, MSB byte first, then raise CS.
                S_CFR3, S_PRF0, S_PRF1: begin
                    launch <= 1'b0;
                    // CS may only rise once the final byte has actually left
                    // the shifter. tx_ready is still high during the cycle the
                    // master is latching that byte, so gating on it alone
                    // truncates every transaction by one byte.
                    if (bytes_left == 0) begin
                        if (!spi_tx_valid && !spi_busy) begin
                            cs_n  <= 1'b1;
                            timer <= '0;
                            case (state)
                                S_CFR3: begin io_update <= 1'b1; state <= S_IOUP1; end
                                S_PRF0: begin
                                    shifter    <= {ADDR_PRF1, profile(pow1)};
                                    bytes_left <= 4'd9;
                                    cs_n       <= 1'b0;
                                    state      <= S_PRF1;
                                end
                                default: begin io_update <= 1'b1; state <= S_IOUP2; end
                            endcase
                        end
                    end else if (spi_tx_ready && !spi_tx_valid && !launch) begin
                        spi_tx_data  <= shifter[71:64];
                        spi_tx_valid <= 1'b1;
                        shifter      <= {shifter[63:0], 8'h00};
                        bytes_left   <= bytes_left - 1'b1;
                    end
                end

                S_IOUP1: if (timer == IOUP_CYCLES-1) begin
                    io_update <= 1'b0;
                    timer     <= '0;
                    state     <= S_LOCK;
                end else timer <= timer + 1'b1;

                // Wait for the PLL, but never hang: a timeout is reported so
                // the console can say "no reference clock" instead of the
                // design sitting silently forever.
                S_LOCK: begin
                    if (pll_lock) begin
                        shifter    <= {ADDR_PRF0, profile(pow0)};
                        bytes_left <= 4'd9;
                        cs_n       <= 1'b0;
                        launch     <= 1'b1;
                        state      <= S_PRF0;
                    end else if (timer == LOCK_CYCLES-1) begin
                        lock_timeout <= 1'b1;
                        shifter      <= {ADDR_PRF0, profile(pow0)};
                        bytes_left   <= 4'd9;
                        cs_n         <= 1'b0;
                        launch       <= 1'b1;
                        state        <= S_PRF0;   // carry on; 40 MHz still works
                    end else timer <= timer + 1'b1;
                end

                S_IOUP2: if (timer == IOUP_CYCLES-1) begin
                    io_update <= 1'b0;
                    state     <= S_DONE;
                end else timer <= timer + 1'b1;

                default: state <= S_IDLE;
            endcase
        end
    end
endmodule

`default_nettype wire
