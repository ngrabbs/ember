// ---------------------------------------------------------------------------
// prbs7_check - PRBS-7 checker with lock detection and error counting
//
// EMBER experimental S-band payload, milestone M0.
//
// Consumes a received bit stream and counts mismatches against the PRBS-7
// sequence defined in prbs7_gen.sv. It is a FREE-RUNNING checker: once locked
// it predicts each bit from its own history rather than from received bits, so
// one channel error produces exactly one counted error. A self-synchronising
// checker (one that shifts the received bit in) would instead multiply a
// single channel error into three counted errors and would never report a loss
// of lock, which makes it the wrong choice for bit-error measurement.
//
// Prediction uses the identity implied by prbs7_gen's convention:
//
//     b[k+7] = b[k] XOR b[k+1]
//
// so the next expected bit is sr[6] XOR sr[5], where sr holds the last seven
// bits of the sequence with the oldest in sr[6].
//
// Lock state machine:
//
//     HUNT    shift LOAD_BITS received bits into sr to acquire a phase
//     VERIFY  free-run and require LOCK_THRESHOLD consecutive correct
//             predictions before declaring lock; any mismatch returns to HUNT.
//             This is what stops a random seven-bit load from being mistaken
//             for a lock.
//     LOCKED  count checked bits and errors
//
// Loss of lock uses a leaky bucket rather than a run of consecutive errors.
// After a bit slip the received stream is a different phase of the same
// sequence, so predictions fail at random with probability one half and a
// consecutive-error counter would take hundreds of bits to trip. The bucket
// fills on each error and is emptied by DECAY_BITS consecutive good bits, so a
// slip unlocks in tens of bits while an isolated error decays away and leaves
// lock intact.
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module prbs7_check #(
    parameter int unsigned LOCK_THRESHOLD = 32,  // good predictions to lock
    parameter int unsigned LOSS_THRESHOLD = 8,   // bucket level that unlocks
    parameter int unsigned DECAY_BITS     = 64,  // good bits that empty the bucket
    parameter int unsigned BIT_COUNT_W    = 48,
    parameter int unsigned ERR_COUNT_W    = 32,
    parameter int unsigned LOSS_COUNT_W   = 16
) (
    input  logic                    clk,
    input  logic                    rst,         // synchronous, active high
    input  logic                    en,          // rx_bit is valid this cycle
    input  logic                    rx_bit,
    output logic                    locked,
    output logic [BIT_COUNT_W-1:0]  bit_count,   // bits checked while locked
    output logic [ERR_COUNT_W-1:0]  error_count, // mismatches while locked
    output logic [LOSS_COUNT_W-1:0] loss_count   // lock-loss events
);

    localparam int unsigned LOAD_BITS = 7;

    typedef enum logic [1:0] {
        HUNT   = 2'd0,
        VERIFY = 2'd1,
        LOCKED = 2'd2
    } state_e;

    state_e state;

    logic [6:0] sr;          // last seven sequence bits, oldest in sr[6]
    logic       predicted;
    logic       match;

    // Counter widths and their terminal values, so every comparison below is
    // between operands of the same width. An unsized 32-bit constant on the
    // right of one of these would compare correctly but hide a genuine width
    // mistake in the surrounding code.
    localparam int unsigned LOAD_W  = $clog2(LOAD_BITS+1);
    localparam int unsigned LOCK_W  = $clog2(LOCK_THRESHOLD+1);
    localparam int unsigned LOSS_W  = $clog2(LOSS_THRESHOLD+1);
    localparam int unsigned DECAY_W = $clog2(DECAY_BITS+1);

    localparam logic [LOAD_W-1:0]  LOAD_LAST  = LOAD_W'(LOAD_BITS - 1);
    localparam logic [LOCK_W-1:0]  LOCK_LAST  = LOCK_W'(LOCK_THRESHOLD - 1);
    localparam logic [LOSS_W-1:0]  LOSS_LAST  = LOSS_W'(LOSS_THRESHOLD - 1);
    localparam logic [DECAY_W-1:0] DECAY_LAST = DECAY_W'(DECAY_BITS - 1);

    logic [LOAD_W-1:0]  load_count;
    logic [LOCK_W-1:0]  good_run;
    logic [LOSS_W-1:0]  bucket;
    logic [DECAY_W-1:0] decay_run;

    assign predicted = sr[6] ^ sr[5];
    assign match     = (rx_bit == predicted);
    assign locked    = (state == LOCKED);

    always_ff @(posedge clk) begin
        if (rst) begin
            state       <= HUNT;
            sr          <= '0;
            load_count  <= '0;
            good_run    <= '0;
            bucket      <= '0;
            decay_run   <= '0;
            bit_count   <= '0;
            error_count <= '0;
            loss_count  <= '0;
        end else if (en) begin
            case (state)

                // Acquire a phase by shifting received bits in. After
                // LOAD_BITS bits, sr holds the seven sequence bits that
                // predict the next one.
                HUNT: begin
                    sr <= {sr[5:0], rx_bit};
                    if (load_count == LOAD_LAST) begin
                        load_count <= '0;
                        good_run   <= '0;
                        state      <= VERIFY;
                    end else begin
                        load_count <= load_count + 1'b1;
                    end
                end

                // Free-run and demand a clean run before trusting the phase.
                VERIFY: begin
                    sr <= {sr[5:0], predicted};
                    if (match) begin
                        if (good_run == LOCK_LAST) begin
                            good_run  <= '0;
                            bucket    <= '0;
                            decay_run <= '0;
                            state     <= LOCKED;
                        end else begin
                            good_run <= good_run + 1'b1;
                        end
                    end else begin
                        // Wrong phase. Restart acquisition from this bit.
                        sr         <= {sr[5:0], rx_bit};
                        load_count <= '0;
                        good_run   <= '0;
                        state      <= HUNT;
                    end
                end

                // Measure. bit_count and error_count only advance here, so a
                // reported error rate is always over bits that were actually
                // being checked.
                LOCKED: begin
                    sr        <= {sr[5:0], predicted};
                    bit_count <= bit_count + 1'b1;

                    if (match) begin
                        if (decay_run == DECAY_LAST) begin
                            decay_run <= '0;
                            bucket    <= '0;
                        end else begin
                            decay_run <= decay_run + 1'b1;
                        end
                    end else begin
                        error_count <= error_count + 1'b1;
                        decay_run   <= '0;
                        if (bucket == LOSS_LAST) begin
                            bucket     <= '0;
                            loss_count <= loss_count + 1'b1;
                            load_count <= '0;
                            sr         <= {sr[5:0], rx_bit};
                            state      <= HUNT;
                        end else begin
                            bucket <= bucket + 1'b1;
                        end
                    end
                end

                default: state <= HUNT;
            endcase
        end
    end

`ifndef SYNTHESIS
    initial begin
        if (LOCK_THRESHOLD < 1)
            $fatal(1, "prbs7_check: LOCK_THRESHOLD must be at least 1");
        if (LOSS_THRESHOLD < 1)
            $fatal(1, "prbs7_check: LOSS_THRESHOLD must be at least 1");
        if (DECAY_BITS < 1)
            $fatal(1, "prbs7_check: DECAY_BITS must be at least 1");
    end
`endif

endmodule

`default_nettype wire
