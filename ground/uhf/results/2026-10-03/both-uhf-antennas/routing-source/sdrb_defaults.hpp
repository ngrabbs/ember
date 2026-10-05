//
// Copyright 2018 Ettus Research, a National Instruments Company
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

#ifndef INCLUDED_SDRB_DEFAULTS_HPP
#define INCLUDED_SDRB_DEFAULTS_HPP

#include <cstdint>
#include "ad9361_client.h"

namespace mpm { namespace types { namespace sdrb {

using namespace uhd::usrp;

// RX thresholds retain C/B/A ordering; they are route policy, not filter qualification.
class sdrb_ad9361_client_t : public uhd::usrp::ad9361_params
{
public:
    ~sdrb_ad9361_client_t() {}
    double get_band_edge(frequency_band_t band)
    {
        switch (band) {
            case AD9361_RX_BAND0:
                return 1.2e9;
            case AD9361_RX_BAND1:
                return 2.6e9;
            case AD9361_TX_BAND0:
                // Pin native TX to A (register 0x004 bit 6 clear), including UHF.
                return 0;
            default:
                return 0;
        }
    }
    clocking_mode_t get_clocking_mode()
    {
        return clocking_mode_t::AD9361_XTAL_N_CLK_PATH;
    }
    digital_interface_mode_t get_digital_interface_mode()
    {
        return AD9361_DDR_FDD_LVCMOS;
    }
    digital_interface_delays_t get_digital_interface_timing()
    {
        digital_interface_delays_t delays;
        delays.rx_clk_delay  = 0;
        delays.rx_data_delay = 0xF;
        delays.tx_clk_delay  = 0;
        delays.tx_data_delay = 0xF;
        return delays;
    }
};

}}} // namespace mpm::types::sdrb

#endif // INCLUDED_SDRB_DEFAULTS_HPP
