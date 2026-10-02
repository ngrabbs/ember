#pragma once
/* Experimental application requests, distinct from diagnostic ECHO.
 * RF_WINDOW ACK confirms a bounded window was admitted, not registration.
 * SEND ACK confirms modem final OK, not ground reception. No automatic retry. */
#define UL_RF_WINDOW 0x10
#define UL_RF_WINDOW_ACK 0x11
#define UL_SEND_PACKET 0x12
#define UL_MODEM_ACCEPTED 0x13
#define UL_LINK_STATUS 0x14
#define UL_LINK_STATUS_ACK 0x15
#define CF_RF_WINDOW 0x74
#define CF_RF_WINDOW_ACK 0x75
#define CF_SEND_PACKET 0x76
#define CF_MODEM_ACCEPTED 0x77
#define CF_LINK_STATUS 0x78
#define CF_LINK_STATUS_ACK 0x79
#define UL_ERR_NOT_READY 8
#define UL_ERR_BUSY 9
#define UL_ERR_MODEM_UNKNOWN 10
#define UL_ERR_MODEM_REJECTED 11
