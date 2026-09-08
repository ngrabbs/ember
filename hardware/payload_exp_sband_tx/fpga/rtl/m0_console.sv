// ---------------------------------------------------------------------------
// m0_console - the readout M0's acceptance criterion actually asked for
//
// The gate is "at least 1,000,000 symbols with zero errors". Until now that
// could only be inferred from a sticky LED: a failure was detectable but not
// quantifiable, and a partial failure late in a long run could not be
// distinguished from a total one. This prints the counters.
//
// Commands, one character each, at 115200 8N1:
//
//   s        status line
//   p0..p3   pattern: zero, one, alternating, PRBS-7
//   r0..r3   symbol rate: 1k, 10k, 100k, 1M
//   e / d    assert / deassert tx_enable
//   z        zero the checker (pulses its reset)
//   k        DDS status: PLL lock, init done, lock timeout, tuning word
//   fXXXXXXXX  set the AD9910 frequency tuning word (8 hex digits) and reload
//   cXXXXXXXX  set CFR3, the REFCLK PLL configuration, and reload. Needed
//              because N depends on the reference: 0538C132 for a 40 MHz
//              reference (N=25), 0538C140 for 31.25 MHz (N=32)
//   i        re-run the AD9910 bring-up sequence
//   ?        command summary
//
// Status format, all values hexadecimal:
//
//   LOCK 1 BITS 000003938700 ERR 00000000 LOSS 0000
//
// The counters are snapshotted the moment 's' arrives, so the three values in
// a line are coherent with each other rather than sampled across the ~4 ms the
// line takes to transmit - at 1 Msym/s the bit count moves by 4000 in that time.
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module m0_console (
    input  wire        clk,
    input  wire        rst,

    input  wire  [7:0] rx_data,
    input  wire        rx_valid,

    output logic [7:0] tx_data,
    output logic       tx_valid,
    input  wire        tx_ready,

    input  wire        locked,
    input  wire [47:0] bit_count,
    input  wire [31:0] error_count,
    input  wire [15:0] loss_count,

    input  wire        dds_lock,
    input  wire        dds_done,
    input  wire        dds_timeout,
    output logic [31:0] dds_ftw,
    output logic [31:0] dds_cfr3,
    output logic       dds_start,

    // Reference-clock generator enable. Defaults OFF: when the DDS runs from
    // its own oscillator, the FPGA must not drive the reference net at all.
    output logic       refclk_en,

    output logic [1:0] pattern_sel,
    output logic [1:0] rate_sel,
    output logic       tx_enable,
    output logic       clear
);
    // The templates hold printable characters only, and CR/LF are appended by
    // index below. Escape sequences in string literals are not portable: Icarus
    // renders "\r" as a literal 'r', which would make simulation and hardware
    // disagree about what is on the wire.
    localparam int TEXT_STATUS = 47;
    localparam int TEXT_BANNER = 58;
    localparam int TEXT_DDS    = 42;
    localparam int STATUS_LEN  = TEXT_STATUS + 2;
    localparam int BANNER_LEN  = TEXT_BANNER + 2;
    localparam int DDS_LEN     = TEXT_DDS + 2;

    localparam logic [7:0] CR = 8'h0D;
    localparam logic [7:0] LF = 8'h0A;

    localparam logic [8*TEXT_STATUS-1:0] STATUS_T =
        "LOCK 0 BITS 000000000000 ERR 00000000 LOSS 0000";
    localparam logic [8*TEXT_BANNER-1:0] BANNER =
        "EMBER M0 s p0-3 r0-3 e d z k i x0-1 fXXXXXXXX cXXXXXXXX ? ";
    localparam logic [8*TEXT_DDS-1:0] DDS_T =
        "DDS LOCK 0 DONE 0 TMO 0 REF 0 FTW 00000000";

    typedef enum logic [3:0] { IDLE, ARG_P, ARG_R, ARG_F, ARG_X, SEND } state_e;
    state_e state;

    logic [1:0]  msg_sel;          // 0 status, 1 banner, 2 DDS
    logic [6:0]  idx;
    logic [2:0]  hex_count;
    logic [27:0] hex_acc;   // 7 nibbles; the 8th completes the word
    logic        hex_target;  // 0 = FTW, 1 = CFR3
    logic        snap_dl, snap_dd, snap_dt, snap_dr;
    logic [31:0] snap_ftw;
    logic [47:0] snap_bits;
    logic [31:0] snap_err;
    logic [15:0] snap_loss;
    logic        snap_lock;

    function automatic logic [7:0] nib2asc(input logic [3:0] n);
        return (n < 4'd10) ? (8'h30 + {4'b0, n}) : (8'h41 + {4'b0, n} - 8'd10);
    endfunction

    // Character for the current index of the current message.
    logic [7:0] ch;
    logic [6:0] n;                     // nibble position, MSB first
    always_comb begin
        n  = 7'd0;
        ch = 8'h20;
        if (msg_sel == 2'd1) begin
            if      (idx == 7'(TEXT_BANNER))     ch = CR;
            else if (idx == 7'(TEXT_BANNER + 1)) ch = LF;
            else ch = BANNER[(TEXT_BANNER-1-int'(idx))*8 +: 8];
        end else if (msg_sel == 2'd2) begin
            if      (idx == 7'(TEXT_DDS))     ch = CR;
            else if (idx == 7'(TEXT_DDS + 1)) ch = LF;
            else if (idx == 7'd9)  ch = snap_dl ? "1" : "0";
            else if (idx == 7'd16) ch = snap_dd ? "1" : "0";
            else if (idx == 7'd22) ch = snap_dt ? "1" : "0";
            else if (idx == 7'd28) ch = snap_dr ? "1" : "0";
            else if (idx >= 7'd34 && idx <= 7'd41) begin
                n  = 7'd41 - idx;
                ch = nib2asc(snap_ftw[int'(n)*4 +: 4]);
            end else ch = DDS_T[(TEXT_DDS-1-int'(idx))*8 +: 8];
        end else if (idx == 7'(TEXT_STATUS)) begin
            ch = CR;
        end else if (idx == 7'(TEXT_STATUS + 1)) begin
            ch = LF;
        end else if (idx == 7'd5) begin
            ch = snap_lock ? "1" : "0";
        end else if (idx >= 7'd12 && idx <= 7'd23) begin
            n  = 7'd23 - idx;
            ch = nib2asc(snap_bits[int'(n)*4 +: 4]);
        end else if (idx >= 7'd29 && idx <= 7'd36) begin
            n  = 7'd36 - idx;
            ch = nib2asc(snap_err[int'(n)*4 +: 4]);
        end else if (idx >= 7'd43 && idx <= 7'd46) begin
            n  = 7'd46 - idx;
            ch = nib2asc(snap_loss[int'(n)*4 +: 4]);
        end else begin
            ch = STATUS_T[(TEXT_STATUS-1-int'(idx))*8 +: 8];
        end
    end

    logic [6:0] msg_len;
    always_comb begin
        case (msg_sel)
            2'd1:    msg_len = 7'(BANNER_LEN);
            2'd2:    msg_len = 7'(DDS_LEN);
            default: msg_len = 7'(STATUS_LEN);
        endcase
    end

    // 0-9 A-F a-f to a nibble; anything else aborts the entry.
    function automatic logic is_hex(input logic [7:0] c);
        return (c >= "0" && c <= "9") || (c >= "A" && c <= "F") || (c >= "a" && c <= "f");
    endfunction
    function automatic logic [3:0] asc2nib(input logic [7:0] c);
        if (c <= "9")      return c[3:0];
        else if (c <= "F") return 4'(c - "A") + 4'd10;
        else               return 4'(c - "a") + 4'd10;
    endfunction

    always_ff @(posedge clk) begin
        tx_valid  <= 1'b0;
        clear     <= 1'b0;
        dds_start <= 1'b0;

        if (rst) begin
            state       <= IDLE;
            idx         <= '0;
            msg_sel     <= 2'd0;
            pattern_sel <= 2'b11;      // PRBS-7 is the useful default
            rate_sel    <= 2'b00;
            tx_enable   <= 1'b1;
            dds_ftw     <= 32'h028F_5C29;   // 10 MHz at a 1 GHz SYSCLK
            // N=25, for the module's own 40 MHz oscillator - 40 x 25 = 1 GHz.
            // This pairs with refclk_en = 0 below: the default configuration is
            // the DDS clocking itself, with the FPGA off the reference net.
            // For the FPGA-driven 12.5 MHz reference use x1 then c0538C1A0.
            dds_cfr3    <= 32'h0538_C132;
            refclk_en   <= 1'b0;
            hex_count   <= '0;
            hex_target  <= 1'b0;
        end else begin
            case (state)
                IDLE: if (rx_valid) begin
                    case (rx_data)
                        "s", "S": begin
                            snap_bits <= bit_count;
                            snap_err  <= error_count;
                            snap_loss <= loss_count;
                            snap_lock <= locked;
                            msg_sel   <= 2'd0;
                            idx       <= '0;
                            state     <= SEND;
                        end
                        "?", "h", "H": begin
                            msg_sel <= 2'd1;
                            idx     <= '0;
                            state   <= SEND;
                        end
                        "k", "K": begin
                            snap_dl  <= dds_lock;
                            snap_dd  <= dds_done;
                            snap_dt  <= dds_timeout;
                            snap_dr  <= refclk_en;
                            snap_ftw <= dds_ftw;
                            msg_sel  <= 2'd2;
                            idx      <= '0;
                            state    <= SEND;
                        end
                        "f", "F": begin
                            hex_acc    <= '0;
                            hex_count  <= '0;
                            hex_target <= 1'b0;
                            state      <= ARG_F;
                        end
                        "c", "C": begin
                            hex_acc    <= '0;
                            hex_count  <= '0;
                            hex_target <= 1'b1;
                            state      <= ARG_F;
                        end
                        "i", "I": dds_start <= 1'b1;
                        "x", "X": state     <= ARG_X;
                        "p", "P": state     <= ARG_P;
                        "r", "R": state     <= ARG_R;
                        "e", "E": tx_enable <= 1'b1;
                        "d", "D": tx_enable <= 1'b0;
                        "z", "Z": clear     <= 1'b1;
                        default:  ;                  // ignore anything else
                    endcase
                end

                // x0 releases the reference pin, x1 drives it. Deliberately
                // explicit rather than a toggle: the wrong state here shorts
                // the FPGA's driver against the DDS module's oscillator, so
                // "what is it now?" must never be part of setting it.
                ARG_X: if (rx_valid) begin
                    if      (rx_data == "0") refclk_en <= 1'b0;
                    else if (rx_data == "1") refclk_en <= 1'b1;
                    state <= IDLE;
                end

                ARG_P: if (rx_valid) begin
                    if (rx_data >= "0" && rx_data <= "3")
                        pattern_sel <= rx_data[1:0];
                    state <= IDLE;
                end

                ARG_R: if (rx_valid) begin
                    if (rx_data >= "0" && rx_data <= "3")
                        rate_sel <= rx_data[1:0];
                    state <= IDLE;
                end

                // Eight hex digits, then load and reload the DDS profiles. A
                // non-hex character aborts rather than loading a half-typed
                // tuning word, which would put the carrier somewhere arbitrary.
                ARG_F: if (rx_valid) begin
                    if (!is_hex(rx_data)) begin
                        state <= IDLE;
                    end else begin
                        hex_acc <= {hex_acc[23:0], asc2nib(rx_data)};
                        if (hex_count == 3'd7) begin
                            if (hex_target) dds_cfr3 <= {hex_acc[27:0], asc2nib(rx_data)};
                            else            dds_ftw  <= {hex_acc[27:0], asc2nib(rx_data)};
                            dds_start <= 1'b1;
                            state     <= IDLE;
                        end else begin
                            hex_count <= hex_count + 3'd1;
                        end
                    end
                end

                SEND: if (tx_ready && !tx_valid) begin
                    tx_data  <= ch;
                    tx_valid <= 1'b1;
                    if (idx == msg_len - 7'd1) state <= IDLE;
                    else                       idx   <= idx + 7'd1;
                end

                default: state <= IDLE;
            endcase
        end
    end
`ifndef SYNTHESIS
    // A string literal shorter than its field is silently zero-padded on the
    // LEFT, so the message would begin with NULs and every index would be
    // wrong. Catching it here turns a puzzling terminal into a clear error.
    initial begin
        if (STATUS_T[8*TEXT_STATUS-1 -: 8] == 8'h00)
            $fatal(1, "m0_console: STATUS_T is shorter than TEXT_STATUS (%0d)", TEXT_STATUS);
        if (BANNER[8*TEXT_BANNER-1 -: 8] == 8'h00)
            $fatal(1, "m0_console: BANNER is shorter than TEXT_BANNER (%0d)", TEXT_BANNER);
        if (DDS_T[8*TEXT_DDS-1 -: 8] == 8'h00)
            $fatal(1, "m0_console: DDS_T is shorter than TEXT_DDS (%0d)", TEXT_DDS);
    end
`endif

endmodule

`default_nettype wire
