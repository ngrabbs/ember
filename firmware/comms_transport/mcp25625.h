#ifndef EMBER_MCP25625_H
#define EMBER_MCP25625_H
#include "can_fragment.h"
typedef struct {
    bool ready, pending;
    uint32_t sent_at, tx_ok, tx_fail, tx_timeout, rx, rx_bad, rx_overflow;
} mcp_state;
bool mcp_init(mcp_state *s);
bool mcp_mode(mcp_state *s,uint8_t mode);
bool mcp_send(mcp_state *s,const cf_frame *frame);
void mcp_poll_tx(mcp_state *s,uint32_t now);
bool mcp_receive(mcp_state *s,cf_frame *frame);
uint8_t mcp_register(uint8_t reg);
#endif
