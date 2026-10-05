import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'ground/ember'))
from lte_diagnostics import decode_diagnostics


class ModemDiagnosticDecode(unittest.TestCase):
    def test_error_evidence_survives_off_status(self):
        p=bytearray(96);p[16]=1;p[18]=1;p[19]=2;p[21]=10;p[22]=7;p[23]=5
        struct.pack_into('>I',p,24,173);p[44]=3;p[45]=2;p[48:51]=b'173'
        d=decode_diagnostics(p)
        self.assertEqual(d['state'],0)
        self.assertEqual(d['cme_number'],173)
        self.assertEqual(d['error_text'],'173')
        self.assertTrue(d['prompt_seen'])
        self.assertTrue(d['failure_seen'])
        self.assertFalse(d['final_send_ok'])
        self.assertEqual(d['failure_cereg'],2)
        self.assertRaises(ValueError,decode_diagnostics,p[:16])
        p[44]=48;self.assertRaises(ValueError,decode_diagnostics,p)
        p[44]=3;p[51]=1;self.assertRaises(ValueError,decode_diagnostics,p)
