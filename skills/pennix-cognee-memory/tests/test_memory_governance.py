import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from cognee_client import CogneeClient, CogneeError


class MemoryGovernanceTest(unittest.TestCase):
    def test_failed_revision_preserves_old_record_and_promotion_requires_approval(self):
        client = CogneeClient('https://memory.test', 'test-key', 'project', 'dataset')
        old_id = '11111111-1111-4111-8111-111111111111'
        with (
            mock.patch.object(client, '_data', return_value=[{'id': old_id}]),
            mock.patch.object(client, 'remember', side_effect=CogneeError('not exact-readable')),
            mock.patch.object(client, 'delete_record') as delete,
        ):
            with self.assertRaises(CogneeError):
                client.revise_record(old_id, 'corrected', task='task', host_session='host', source='file')
            delete.assert_not_called()
        with mock.patch.object(client, '_request') as request:
            with self.assertRaises(CogneeError):
                client.promote_record(old_id, scope='user', approval_ref='', task='task', host_session='host')
            request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
