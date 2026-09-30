#!/usr/bin/env python3
"""Private operation records only. The host owns all MCP calls and credentials."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from workspace_lib import read_json, write_json, digest, immutable_copy, scoped_path, locked


@locked
def prepare(project, service, account, action, revision_id, remote_id=None, base_fingerprint=None):
    if not all([service, account, action, revision_id]):
        raise ValueError('Service, account, action and revision required')
    rows = read_json(project / '版本记录/revisions.json')['revisions']
    matches = [r for r in rows if r['id'] == revision_id]
    if len(matches) != 1:
        raise ValueError('Unknown revision')
    revision = matches[0]
    if digest(scoped_path(project, revision['path'])) != revision['sha256']:
        raise ValueError('Revision content has changed')
    if action == 'update' and not (remote_id and base_fingerprint):
        raise ValueError('Updates require a target and a pre-read fingerprint')
    key = hashlib.sha256(json.dumps([service, account, action, revision_id, revision['sha256'], remote_id, base_fingerprint], ensure_ascii=False).encode()).hexdigest()[:24]
    path = project / '外部操作记录/operations' / (key + '.json')
    if path.exists():
        existing = read_json(path)
        return dict(existing, existing_operation=True, retry_requires_reconciliation=True)
    item = {'schema_version': 1, 'operation_id': key, 'service': service, 'account_alias': account,
            'action': action, 'revision_id': revision_id, 'local_sha256': revision['sha256'],
            'remote_id': remote_id, 'base_fingerprint': base_fingerprint, 'status': 'prepared',
            'created_at': datetime.now(timezone.utc).isoformat(), 'events': []}
    write_json(path, item)
    return item


@locked
def record_result(project, operation_id, status, evidence_file, remote_id=None):
    if status not in {'submitted', 'verified', 'failed', 'unknown', 'conflict'}:
        raise ValueError('Unsupported operation state')
    path = scoped_path(project, '外部操作记录/operations/' + operation_id + '.json')
    item = read_json(path)
    if item['status'] == 'verified':
        raise ValueError('Verified receipt is immutable; prepare another operation for a changed revision')
    evidence = read_json(evidence_file)
    if evidence.get('source') != 'live_mcp' or evidence.get('service') != item['service']:
        raise ValueError('Use the actual host MCP receipt for this service')
    if evidence.get('operation_id') != operation_id or evidence.get('account_alias') != item['account_alias']:
        raise ValueError('Receipt belongs to another operation or account')
    if status == 'verified' and not (evidence.get('readback_matches') is True and evidence.get('response') and evidence.get('local_sha256') == item['local_sha256'] and evidence.get('remote_id') == (remote_id or item['remote_id']) and evidence.get('remote_id')):
        raise ValueError('Verified state requires readback/query evidence')
    rel = '外部操作记录/evidence/' + operation_id + '-' + str(len(item['events']) + 1) + '.json'
    immutable_copy(evidence_file, scoped_path(project, rel))
    item['events'].append({'status': status, 'evidence': rel, 'sha256': digest(evidence_file)})
    item['status'] = status
    if remote_id: item['remote_id'] = remote_id
    write_json(path, item)
    return item


def main():
    from writing_workspace import resolve_project
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, default=Path('workspace'));p.add_argument('--project', required=True)
    s = p.add_subparsers(dest='command', required=True)
    prep = s.add_parser('prepare')
    for name in ['service','account','action','revision']: prep.add_argument('--'+name, required=True)
    prep.add_argument('--remote-id');prep.add_argument('--base-fingerprint')
    record = s.add_parser('record')
    for name in ['operation','status','evidence']:record.add_argument('--'+name,required=True)
    record.add_argument('--remote-id')
    a=p.parse_args();project=resolve_project(a.workspace,a.project)
    if a.command=='prepare':result=prepare(project,a.service,a.account,a.action,a.revision,a.remote_id,a.base_fingerprint)
    else:result=record_result(project,a.operation,a.status,a.evidence,a.remote_id)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
