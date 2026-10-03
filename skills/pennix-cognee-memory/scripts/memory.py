#!/usr/bin/env python3
"""Explicit semantic operations; ordinary automatic memory stays official."""
import argparse
import json
from pathlib import Path
from cognee_client import CogneeClient, CogneeError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, required=True)
    actions = parser.add_subparsers(dest='action', required=True)
    for action in ('remember', 'revise', 'promote'):
        item = actions.add_parser(action)
        item.add_argument('--task', required=True)
        item.add_argument('--host-session', required=True)
        if action != 'remember':
            item.add_argument('--data-id', required=True)
        if action != 'promote':
            item.add_argument('--text-file', type=Path, required=True)
            item.add_argument('--source', required=True)
        else:
            item.add_argument('--scope', choices=['cross_project', 'user'], required=True)
            item.add_argument('--approval-ref', required=True)
    for action in ('raw', 'delete', 'revoke'):
        item = actions.add_parser(action)
        item.add_argument('--data-id', required=True)
    recall = actions.add_parser('recall')
    recall.add_argument('--query', required=True)
    improve = actions.add_parser('improve')
    improve.add_argument('--session-id', action='append', default=[])
    args = parser.parse_args()
    try:
        client = CogneeClient.for_project(args.project_root)
        if args.action in {'remember', 'revise'}:
            text = args.text_file.read_text(encoding='utf-8')
            kwargs = dict(task=args.task, host_session=args.host_session, source=args.source)
            result = client.remember(text, **kwargs) if args.action == 'remember' else client.revise_record(args.data_id, text, **kwargs)
        elif args.action == 'promote':
            result = client.promote_record(args.data_id, scope=args.scope, approval_ref=args.approval_ref,
                                          task=args.task, host_session=args.host_session)
        elif args.action in {'delete', 'revoke'}:
            client.delete_record(args.data_id)
            result = {'data_id': args.data_id, 'source_deleted': True,
                      'derived_absence_requires_recall_verification': True}
        elif args.action == 'raw':
            result = {'data_id': args.data_id, 'content': client._raw(args.data_id)}
        elif args.action == 'recall':
            result = client.recall(args.query)
        else:
            result = client.improve(session_ids=args.session_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (CogneeError, OSError, ValueError) as error:
        parser.exit(2, f'Cognee operation failed: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
