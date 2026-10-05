"""Decode version1 cached Walter diagnostics; never issues modem commands."""
import struct


def decode_diagnostics(packet):
    if len(packet) != 96 or packet[16] != 1:
        raise ValueError('Unsupported Walter diagnostic size/version')
    length, kind = packet[44], packet[45]
    if length > 47 or kind > 3 or packet[48+length] != 0:
        raise ValueError('Malformed modem error text')
    flags = packet[23]
    number = struct.unpack_from('>I', packet, 24)[0]
    words = struct.unpack_from('>IIII', packet, 28)
    return dict(version=1, state=packet[0], error=packet[2], registered=packet[3],
                window_ms=struct.unpack_from('>I', packet, 4)[0],
                last_cereg=packet[17], send_cereg=packet[18], failure_cereg=packet[19],
                last_command=packet[20], failure_command=packet[21], failure_state=packet[22],
                prompt_seen=bool(flags & 1), final_send_ok=bool(flags & 2),
                failure_seen=bool(flags & 4), socket_open_ok_observed=bool(flags & 8),
                error_text_truncated=bool(flags & 32),
                cme_number=None if number == 0xffffffff else number,
                send_elapsed_ms=words[0], registration_losses=words[1],
                last_cereg_elapsed_ms=words[2], uart_send_request=words[3],
                error_kind=('none','ERROR','numeric_CME','text_CME')[kind],
                error_text=packet[48:48+length].decode('ascii',errors='replace'))
