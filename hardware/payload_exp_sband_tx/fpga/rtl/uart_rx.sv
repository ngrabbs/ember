// ---------------------------------------------------------------------------
// uart_rx - 8N1 receiver
//
// Synchronises the incoming line, waits half a bit after the start edge to
// confirm it is not a glitch, then samples each bit at its midpoint. A framing
// error (stop bit not high) drops the byte rather than reporting garbage.
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module uart_rx #(
    parameter int unsigned CLOCK_HZ = 125_000_000,
    parameter int unsigned BAUD     = 115_200
) (
    input  wire        clk,
    input  wire        rst,
    input  wire        rx,
    output logic [7:0] data,
    output logic       valid,
    output logic       frame_error
);
    localparam int unsigned DIVISOR = CLOCK_HZ / BAUD;
    localparam int unsigned HALF    = DIVISOR / 2;
    localparam int unsigned DW      = $clog2(DIVISOR);

    typedef enum logic [1:0] { IDLE, START, DATA, STOP } state_e;
    state_e state;

    logic [1:0]    sync;
    logic [DW-1:0] baud_count;
    logic [2:0]    bit_index;
    logic [7:0]    shifter;

    always_ff @(posedge clk) begin
        sync  <= {sync[0], rx};
        valid <= 1'b0;

        if (rst) begin
            state       <= IDLE;
            sync        <= 2'b11;
            baud_count  <= '0;
            bit_index   <= '0;
            frame_error <= 1'b0;
        end else begin
            case (state)
                IDLE: if (!sync[1]) begin        // falling edge = start
                    baud_count <= '0;
                    state      <= START;
                end

                // Half a bit in, the line must still be low. If it is not, the
                // edge was noise, not a start bit.
                START: if (baud_count == DW'(HALF-1)) begin
                    baud_count <= '0;
                    if (!sync[1]) begin
                        bit_index <= '0;
                        state     <= DATA;
                    end else begin
                        state <= IDLE;
                    end
                end else begin
                    baud_count <= baud_count + 1'b1;
                end

                DATA: if (baud_count == DW'(DIVISOR-1)) begin
                    baud_count <= '0;
                    shifter    <= {sync[1], shifter[7:1]};   // LSB first
                    if (bit_index == 3'd7) state <= STOP;
                    else                   bit_index <= bit_index + 1'b1;
                end else begin
                    baud_count <= baud_count + 1'b1;
                end

                STOP: if (baud_count == DW'(DIVISOR-1)) begin
                    baud_count <= '0;
                    state      <= IDLE;
                    if (sync[1]) begin
                        data        <= shifter;
                        valid       <= 1'b1;
                        frame_error <= 1'b0;
                    end else begin
                        frame_error <= 1'b1;     // drop it rather than lie
                    end
                end else begin
                    baud_count <= baud_count + 1'b1;
                end

                default: state <= IDLE;
            endcase
        end
    end
endmodule

`default_nettype wire
