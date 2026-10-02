import base64
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'ground/ember'))
from lte_reliability import compare


class ReliabilityComparison(unittest.TestCase):
    def test_requires_own_packet_in_radio_and_archive_and_modem_off(self):
        host = {'modem_accepted':[{'hex':'010203'}],
                'final_modem_status':'LTE_STATUS state=0 step=8 error=0 registered=0 window_ms=0'}
        radio = {'packets':[{'hex':'010203'}]}
        archive = {'packets':[{'packet':base64.b64encode(b'\x01\x02\x03').decode()}]}
        self.assertTrue(compare(host,radio,archive)['success'])
        self.assertFalse(compare(host,radio,{'packets':[]})['success'])
        self.assertFalse(compare(host,{'packets':[{'hex':'0a0102'}]},archive)['success'])
        self.assertFalse(compare(host,{'packets':[]},archive)['success'])
        host['final_modem_status']='LTE_STATUS state=6 step=8 window_ms=100'
        self.assertFalse(compare(host,radio,archive)['success'])


if __name__ == '__main__':
    unittest.main()
