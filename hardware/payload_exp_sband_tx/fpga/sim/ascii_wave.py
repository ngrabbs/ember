#!/usr/bin/env python3
"""Render a symbol-domain waveform from a testbench VCD, in the terminal.

GTKWave is the real tool, but this needs no display, works over SSH, and is a
fast way to confirm the symbol stream is what it should be. It samples
tx_symbol on every symbol_tick, draws the result, and - for PRBS-7 - checks
the captured bits against the golden sequence at every phase.

    python3 sim/ascii_wave.py build/tb_tx.vcd --last 64
"""
import argparse, re, sys

def parse_vcd(path, wanted):
    """Return {name: [(time, value)]} for the wanted hierarchical names."""
    ids, scope, series, cur = {}, [], {n: [] for n in wanted}, {}
    var_re = re.compile(r'\$var\s+\S+\s+(\d+)\s+(\S+)\s+([^\s\[]+)')
    t = 0
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line.startswith('$scope'):
                scope.append(line.split()[2]); continue
            if line.startswith('$upscope'):
                scope and scope.pop(); continue
            if line.startswith('$var'):
                m = var_re.match(line)
                if m:
                    full = '.'.join(scope + [m.group(3)])
                    if full in wanted:
                        ids[m.group(2)] = full
                continue
            if line[0] == '#':
                t = int(line[1:]); continue
            if line[0] in '01xzXZ' and len(line) > 1:
                vid = line[1:]
                if vid in ids:
                    name = ids[vid]
                    v = line[0]
                    if cur.get(name) != v:
                        cur[name] = v
                        series[name].append((t, v))
    return series

def value_at(changes, t):
    v = 'x'
    for ct, cv in changes:
        if ct > t:
            break
        v = cv
    return v

def draw(vals, width=2):
    top, bot = [], []
    for i, v in enumerate(vals):
        prev = vals[i-1] if i else v
        if v == 1:
            top.append('┌' + '─'*(width-1) if prev == 0 else '─'*width)
            bot.append('┘' + ' '*(width-1) if prev == 0 else ' '*width)
        else:
            top.append('┐' + ' '*(width-1) if prev == 1 else ' '*width)
            bot.append('└' + '─'*(width-1) if prev == 1 else '─'*width)
    return ''.join(top), ''.join(bot)

def prbs7(n, seed=0x7f):
    st = seed
    for _ in range(n):
        yield (st >> 6) & 1
        st = ((st << 1) | (((st >> 6) ^ (st >> 5)) & 1)) & 0x7f

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('vcd')
    ap.add_argument('--top', default='tb_tx_pattern_source')
    ap.add_argument('--last', type=int, default=64, help='symbols to draw')
    ap.add_argument('--width', type=int, default=2, help='columns per symbol')
    a = ap.parse_args()

    tick = f'{a.top}.symbol_tick'
    sym  = f'{a.top}.tx_symbol'
    s = parse_vcd(a.vcd, {tick, sym})
    if not s[tick]:
        sys.exit(f'no {tick} in {a.vcd}')

    # Sample tx_symbol on each rising edge of symbol_tick.
    bits = [(t, value_at(s[sym], t)) for t, v in s[tick] if v == '1']
    bits = [(t, int(v)) for t, v in bits if v in '01']
    if not bits:
        sys.exit('no symbols captured')

    window = bits[-a.last:]
    vals = [v for _, v in window]
    t0, t1 = window[0][0], window[-1][0]
    period = (t1 - t0) / max(1, len(window) - 1)

    print(f'\n  {len(bits)} symbols captured; showing the last {len(vals)}')
    print(f'  symbol period {period:.0f} ps  ->  {1e12/period/1e3:.1f} ksym/s\n')
    top, bot = draw(vals, a.width)
    print('  tx_symbol  ' + top)
    print('             ' + bot)
    print('             ' + ''.join(str(v).ljust(a.width) for v in vals))

    # Is this window a genuine phase of the PRBS-7 sequence?
    golden = list(prbs7(127))
    seq = ''.join(map(str, vals))
    gold2 = ''.join(map(str, golden + golden))
    idx = gold2.find(seq) if len(seq) <= 127 else -1
    print()
    if idx >= 0:
        print(f'  ✓ matches the golden PRBS-7 sequence at phase {idx}')
    else:
        ones = sum(vals)
        if ones in (0, len(vals)):
            print(f'  constant {vals[0]} pattern')
        elif all(vals[i] != vals[i+1] for i in range(len(vals)-1)):
            print('  alternating pattern - square wave at half the symbol rate')
        else:
            print('  not a PRBS-7 phase, not constant, not alternating')
    print()

if __name__ == '__main__':
    main()
