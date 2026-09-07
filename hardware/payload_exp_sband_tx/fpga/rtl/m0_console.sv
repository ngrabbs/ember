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
    localparam int TEXT_BANNER = 60;
    localparam int STATUS_LEN  = TEXT_STATUS + 2;
    localparam int BANNER_LEN  = TEXT_BANNER + 2;

    localparam logic [7:0] CR = 8'h0D;
    localparam logic [7:0] LF = 8'h0A;

    localparam logic [8*TEXT_STATUS-1:0] STATUS_T =
        "LOCK 0 BITS 000000000000 ERR 00000000 LOSS 0000";
    localparam logic [8*TEXT_BANNER-1:0] BANNER =
        "EMBER M0  s=status p0-3=pattern r0-3=rate e/d=enable z=clear";

    typedef enum logic [2:0] { IDLE, ARG_P, ARG_R, SEND } state_e;
    state_e state;

    logic        msg_is_banner;
    logic [6:0]  idx;
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
        if (msg_is_banner) begin
            if      (idx == 7'(TEXT_BANNER))     ch = CR;
            else if (idx == 7'(TEXT_BANNER + 1)) ch = LF;
            else ch = BANNER[(TEXT_BANNER-1-int'(idx))*8 +: 8];
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
    assign msg_len = msg_is_banner ? 7'(BANNER_LEN) : 7'(STATUS_LEN);

    always_ff @(posedge clk) begin
        tx_valid <= 1'b0;
        clear    <= 1'b0;

        if (rst) begin
            state         <= IDLE;
            idx           <= '0;
            msg_is_banner <= 1'b0;
            pattern_sel   <= 2'b11;      // PRBS-7 is the useful default
            rate_sel      <= 2'b00;
            tx_enable     <= 1'b1;
        end else begin
            case (state)
                IDLE: if (rx_valid) begin
                    case (rx_data)
                        "s", "S": begin
                            snap_bits     <= bit_count;
                            snap_err      <= error_count;
                            snap_loss     <= loss_count;
                            snap_lock     <= locked;
                            msg_is_banner <= 1'b0;
                            idx           <= '0;
                            state         <= SEND;
                        end
                        "?", "h", "H": begin
                            msg_is_banner <= 1'b1;
                            idx           <= '0;
                            state         <= SEND;
                        end
                        "p", "P": state     <= ARG_P;
                        "r", "R": state     <= ARG_R;
                        "e", "E": tx_enable <= 1'b1;
                        "d", "D": tx_enable <= 1'b0;
                        "z", "Z": clear     <= 1'b1;
                        default:  ;                  // ignore anything else
                    endcase
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
endmodule

`default_nettype wire
