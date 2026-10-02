#!/usr/bin/env python3
"""Summarize OAI random-access evidence without printing subscriber identities."""
import argparse
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('logs', nargs='+', type=Path)
args = parser.parse_args()
for path in args.logs:
    responses = []
    released = set()
    counts = dict(ccch_decodes=0, harq0_dtx=0, slot_exhaustion=0, msg4_assert=0,
                  msg4_retries=0, msg4_exhausted=0, msg4_acknowledged=0,
                  rrc_setup_complete=0, downlink_exhaustion=0,
                  reestablishment_reject_acknowledged=0, missing_dedicated_config=0,
                  ccch_response_timeouts=0)
    exit_code = None
    with path.open(errors='replace') as source:
        for line in source:
            match = re.search(r'Generating RAR BR .*?CRNTI ([0-9a-f]+)', line)
            if match:
                responses.append(match.group(1))
            match = re.search(r'remove UE ([0-9a-f]+) from freeList', line)
            if match:
                released.add(match.group(1))
            counts['ccch_decodes'] += 'Decoding UL CCCH' in line
            counts['harq0_dtx'] += 'Received 4 for harq_pid 0' in line
            counts['slot_exhaustion'] += 'No existing UE ULSCH' in line
            counts['msg4_assert'] += 'Msg4 Retransmissions not handled' in line
            counts['msg4_retries'] += 'Scheduling BL/CE Msg4 retry' in line
            counts['msg4_exhausted'] += 'BL/CE Msg4 retries exhausted' in line
            counts['msg4_acknowledged'] += 'Msg4 acknowledged' in line
            counts['rrc_setup_complete'] += 'processing LTE_RRCConnectionSetupComplete' in line
            counts['downlink_exhaustion'] += 'no free or exiting dlsch_context' in line
            counts['reestablishment_reject_acknowledged'] += 'BL/CE reestablishment reject acknowledged' in line
            counts['missing_dedicated_config'] += 'UE_template->physicalConfigDedicated is null' in line
            counts['ccch_response_timeouts'] += 'BL/CE Msg4 CCCH response timed out' in line
            match = re.search(r'EXIT code=(-?\d+)', line)
            if match:
                exit_code = int(match.group(1))
    print(json.dumps(dict(log=path.name, br_responses=len(responses),
                          br_contexts_released=sum(rnti in released for rnti in responses),
                          **counts, exit_code=exit_code)))
