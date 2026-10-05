"""Admission isolation, duplicate suppression and bounded overflow behavior."""
import copy,json,queue,unittest
from pathlib import Path
from can_forward import Admission

class AdmissionTests(unittest.TestCase):
    def setUp(self):
        proof=json.loads((Path(__file__).parent/'results/2026-10-03/evidence/rx-03.json').read_text())['packets'][0]
        self.record=dict(outcome='VALIDATED_AND_RECORDED',application_replies_enabled=False,
            sender_boot=proof['decoded']['header']['source_boot_id'],request=1,hex=proof['hex'])
    def test_duplicate_not_queued_again(self):
        q=queue.Queue(maxsize=2);a=Admission(q)
        self.assertEqual(a.admit(self.record),'QUEUED');self.assertEqual(a.admit(self.record),'DUPLICATE')
        self.assertEqual(q.qsize(),1)
    def test_full_queue_no_retry(self):
        q=queue.Queue(maxsize=1);q.put('occupied');a=Admission(q)
        self.assertEqual(a.admit(self.record),'QUEUE_FULL');q.get()
        self.assertEqual(a.admit(self.record),'DUPLICATE');self.assertTrue(q.empty())
    def test_invalid_or_active_records_not_admitted(self):
        for changes in ({'hex':'00'},{'sender_boot':1},{'application_replies_enabled':True},{'outcome':'OTHER'}):
            q=queue.Queue(maxsize=2);a=Admission(q);r=copy.deepcopy(self.record);r.update(changes)
            self.assertEqual(a.admit(r),'REJECTED');self.assertTrue(q.empty())

if __name__=='__main__':unittest.main()
