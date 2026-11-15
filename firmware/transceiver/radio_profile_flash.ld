/* End of the image must precede the final two 4 KiB sectors of Pico flash. */
ASSERT(__flash_binary_end <= 0x101fe000, "Transceiver image overlaps radio profile storage")
