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

    def test_approved_scope_refuses_missing_duplicate_and_foreign_owner_without_writes(self):
        client = CogneeClient('https://memory.test', 'test-key', 'project', 'dataset')
        principal = '11111111-1111-4111-8111-111111111111'
        row = {'name': 'pennix-approved-user-' + principal[:12],
               'id': '22222222-2222-4222-8222-222222222222', 'ownerId': principal}
        with mock.patch.object(client, '_request', return_value={'id': principal}) as request:
            for rows in ([], [row, row], [{**row, 'ownerId': 'foreign'}]):
                with mock.patch.object(client, '_datasets', return_value=rows):
                    with self.assertRaises(CogneeError):
                        client.for_scope('user')
            with mock.patch.object(client, '_datasets', return_value=[row]):
                self.assertEqual(client.for_scope('user').dataset_id, row['id'])
            self.assertTrue(all(call.args[0] == 'GET' for call in request.call_args_list))


if __name__ == '__main__':
    unittest.main()
