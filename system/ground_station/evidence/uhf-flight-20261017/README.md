# UHF downlink into flight EMBER — October 17, 2026

The existing COMMS board firmware 0.30.0 and LibreSDR receiver 2.2.0 delivered
13/13 fresh packets through flight `ember` / `uhf-tm-in`. One COMMS identity and
three cycles of IHU heartbeat, system, EPS and device status were compared byte
for byte with the board console, RF decoder and Yamcs archive. This is a finite
bench downlink result; no Yamcs UHF uplink was added or tested.

`result.json` owns the settings, identities, archive witnesses and limitations.
`rx-native.json`, `session.json` and `packets.jsonl` are unmodified receiver records;
`ihu.txt` and `comms.txt` are the console records. `rx-2ma.json` preserves a failed
standalone heartbeat trial at 2 mA Si5351 drive; `rx-4ma.json` preserves the
successful 4 mA repeat. The full CAN/RF service uses the established 4 mA setting.
These trials do not isolate or qualify the hardware phase/drive behavior.

Raw IQ remains privately on the Pi at the path in `result.json`.
`run_native.py` records the exact host console orchestration used for the full
run, including exclusive serial ownership and finally-block cleanup. It assumes
the receiver is already ready and the existing board wiring/profile is fitted;
it is evidence, not an automatic boot service. `verify.py` compares the saved
records with the live flight archive; it needs access to Pi HTTP8090 and the
retained October 17 history.

The run expired with twelve IHU packets submitted across three cycles. Cleanup
confirmed IHU stop, COMMS service stop, clock output disable and a new CAN HELLO.
The bench bridge was restored. No firmware flash or charger write occurred.
