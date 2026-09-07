#!/usr/bin/env python3
"""Drive the M0 bench: the FPGA over its UART console, the scope over SCPI.

Both ends are remote-controllable, so a capture run needs nobody at the bench.
The console sets pattern and rate; the scope measures and returns screenshots
and waveform data. Nothing here is board-specific beyond the two addresses.
"""
import socket, subprocess, time, sys

SCOPE = ("192.168.1.50", 5555)
UART_HOST = "ngrabbs@192.168.1.252"
UART_DEV = "/dev/ttyUSB0"


# ---------------------------------------------------------------- FPGA console
def console(cmd, settle=0.5):
    """Send a console command, return whatever the FPGA replies."""
    remote = (f"sudo bash -c \"exec 3<>{UART_DEV}; printf '%s' '{cmd}' >&3; "
              f"sleep 0.4; timeout 3 cat <&3\"")
    out = subprocess.run(["ssh", "-o", "BatchMode=yes", UART_HOST, remote],
                         capture_output=True, text=True, timeout=30)
    time.sleep(settle)
    return out.stdout.replace("\r", "").strip()


def setup_uart():
    subprocess.run(["ssh", "-o", "BatchMode=yes", UART_HOST,
                    f"sudo stty -F {UART_DEV} 115200 cs8 -cstopb -parenb raw "
                    f"-echo -crtscts min 0 time 15"], check=True, timeout=30)


# ----------------------------------------------------------------------- scope
class Scope:
    def __init__(self, addr=SCOPE):
        self.s = socket.create_connection(addr, timeout=15)

    def w(self, cmd):
        self.s.sendall(cmd.encode() + b"\n")
        time.sleep(0.05)

    def q(self, cmd, n=8192):
        self.w(cmd)
        return self.s.recv(n).decode(errors="replace").strip()

    def qb(self, cmd):
        """Query returning an IEEE-488.2 definite-length block."""
        self.w(cmd)
        head = b""
        while len(head) < 2:
            head += self.s.recv(2 - len(head))
        assert head[0:1] == b"#", f"bad block header {head!r}"
        ndig = int(head[1:2])
        lenb = b""
        while len(lenb) < ndig:
            lenb += self.s.recv(ndig - len(lenb))
        total = int(lenb)
        buf = b""
        while len(buf) < total:
            chunk = self.s.recv(min(65536, total - len(buf)))
            if not chunk:
                break
            buf += chunk
        self.s.recv(1)                      # trailing newline
        return buf

    def meas(self, item, src="CHANnel1"):
        v = self.q(f":MEASure:ITEM? {item},{src}")
        try:
            f = float(v)
        except ValueError:
            return None
        return None if abs(f) > 9e36 else f   # 9.9e37 is Rigol's "no reading"

    def screenshot(self, path):
        data = self.qb(":DISPlay:DATA? ON,0,PNG")
        open(path, "wb").write(data)
        return len(data)

    def waveform(self, src="CHANnel1"):
        """Screen-mode capture: 1200 points, with x/y scaling applied."""
        self.w(":STOP")
        self.w(f":WAVeform:SOURce {src}")
        self.w(":WAVeform:MODE NORMal")
        self.w(":WAVeform:FORMat BYTE")
        pre = self.q(":WAVeform:PREamble?").split(",")
        xinc, xorig = float(pre[4]), float(pre[5])
        yinc, yorig, yref = float(pre[7]), float(pre[8]), float(pre[9])
        raw = self.qb(":WAVeform:DATA?")
        volts = [(b - yref - yorig) * yinc for b in raw]
        return xinc, xorig, volts


if __name__ == "__main__":
    setup_uart()
    print(console("?"))
    sc = Scope()
    print(sc.q("*IDN?"))
