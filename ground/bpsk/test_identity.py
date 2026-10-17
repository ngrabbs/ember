"""Ensure local edits cannot retain an approved receiver content identity."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import identity

class IdentityTests(unittest.TestCase):
    def test_dictionary_edit_changes_identity_without_version_bump(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'bpsk';root.mkdir()
            for name in identity.FILES:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((identity.ROOT/name).read_bytes())
            with patch.object(identity,'ROOT',root):
                before=identity.identity()
                dictionary=root/'../ember/dictionary.json'
                original=dictionary.read_bytes();dictionary.write_bytes(original+b'\n')
                after=identity.identity()
                self.assertEqual(before['version'],after['version'])
                self.assertNotEqual(before['sha256'],after['sha256'])
                dictionary.write_bytes(original)
                self.assertEqual(before,identity.identity())

if __name__=='__main__':unittest.main()
