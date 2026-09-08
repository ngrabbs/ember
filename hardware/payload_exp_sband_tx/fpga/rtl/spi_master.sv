// ---------------------------------------------------------------------------
// spi_master - byte-oriented SPI mode 0 master
//
// EMBER experimental S-band payload, M1. Vendor-neutral, no primitives.
//
// Mode 0: SCLK idles low, MOSI is driven on the falling edge, and both ends
// sample on the rising edge. That is what the AD9910's serial port expects.
//
// Chip select is deliberately NOT driven here. An AD9910 transaction is one
// instruction byte followed by a variable number of data bytes, all under a
// single CS assertion, and the length depends on which register is addressed.
// Keeping CS with the sequencer means this block stays a dumb shifter and the
// protocol knowledge lives in one place.
//
// SDIO is bidirectional. The AD9910 powers up in 2-wire mode, where read data
// comes back on SDIO rather than SDO, and getting to 3-wire needs a successful
// CFR1 write - which is exactly what you cannot assume when the question is
// "does this part respond at all". So reads are done the way the part powers
// up: `tx_read` releases MOSI for the duration of a byte and captures it.
//
// The alternative, setting CFR1[1] first and reading on SDO, was the original
// plan and was never implemented. It is also circular as a diagnostic: it
// needs a working write before it can verify that writes work.
// ---------------------------------------------------------------------------

`timescale 1ns / 1ps
`default_nettype none

module spi_master #(
    parameter int unsigned CLOCK_HZ = 125_000_000,
    parameter int unsigned SCLK_HZ  =   1_000_000
) (
    input  wire        clk,
    input  wire        rst,

    input  wire  [7:0] tx_data,
    input  wire        tx_valid,
    // Sampled with tx_valid. 1 = this byte is a READ: MOSI is released for the
    // whole byte so the slave can drive the line, and the result appears in
    // rx_data. tx_data is ignored.
    input  wire        tx_read,
    output logic       tx_ready,

    output logic [7:0] rx_data,
    output logic       rx_valid,

    output logic       sclk,
    output logic       mosi,
    output logic       mosi_oe,   // 0 while reading - drive a tri-state here
    input  wire        miso,
    output logic       busy
);
    // Half a SCLK period in system clocks. Integer division truncates, so the
    // realised rate runs slightly fast - 5 MHz requested from 125 MHz gives
    // 5.208 MHz. Unlike a UART, that does not matter: SPI is source
    // synchronous, the clock travels with the data, and only the slave's
    // MAXIMUM rate is a constraint. Round down when choosing SCLK_HZ.
    localparam int unsigned HALF = CLOCK_HZ / (2 * SCLK_HZ);
    localparam int unsigned CW   = (HALF <= 1) ? 1 : $clog2(HALF);

    logic [CW-1:0] div;
    logic          tick;
    logic [2:0]    bit_index;
    logic [6:0]    shift_tx;   // bit 7 goes straight to mosi at load time
    logic [7:0]    shift_rx;
    logic          phase;          // 0 = about to rise, 1 = about to fall
    logic          reading;        // this byte is a read; MOSI is released

    assign mosi_oe  = ~reading;
    assign tx_ready = ~busy;
    assign tick     = (div == CW'(HALF-1));

    always_ff @(posedge clk) begin
        rx_valid <= 1'b0;

        if (rst) begin
            busy      <= 1'b0;
            sclk      <= 1'b0;
            mosi      <= 1'b0;
            div       <= '0;
            phase     <= 1'b0;
            bit_index <= '0;
            reading   <= 1'b0;
        end else if (!busy) begin
            sclk <= 1'b0;
            div  <= '0;
            if (tx_valid) begin
                shift_tx  <= tx_data[6:0];
                mosi      <= tx_data[7];      // MSB first, valid before the edge
                busy      <= 1'b1;
                phase     <= 1'b0;
                bit_index <= '0;
                // Released before the first rising edge, so the slave owns the
                // line for the whole byte rather than for seven eighths of it.
                reading   <= tx_read;
            end
        end else if (!tick) begin
            div <= div + 1'b1;
        end else begin
            div <= '0;
            if (!phase) begin
                // Rising edge: the slave samples MOSI, we sample MISO.
                sclk     <= 1'b1;
                shift_rx <= {shift_rx[6:0], miso};
                phase    <= 1'b1;
            end else begin
                // Falling edge: present the next bit, or finish the byte.
                sclk  <= 1'b0;
                phase <= 1'b0;
                if (bit_index == 3'd7) begin
                    // All eight bits have already been sampled into shift_rx
                    // on the rising edges. Shifting miso in again here would
                    // count the last bit twice.
                    busy     <= 1'b0;
                    rx_data  <= shift_rx;
                    rx_valid <= 1'b1;
                end else begin
                    shift_tx  <= {shift_tx[5:0], 1'b0};
                    mosi      <= shift_tx[6];
                    bit_index <= bit_index + 1'b1;
                end
            end
        end
    end

`ifndef SYNTHESIS
    initial begin
        if (HALF < 2)
            $fatal(1, "spi_master: SCLK_HZ too close to CLOCK_HZ");
    end
`endif
endmodule

`default_nettype wire
