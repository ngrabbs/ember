#!/usr/bin/env python3
"""Inventory first-party documentation and check local Markdown file links.

Run from any directory. This checks files, not external URLs, heading anchors,
engineering correctness, deployed services, CAD, or hardware. Dispositions in
findings.json are editorial decisions; other classifications are content triage.
"""
import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', '.runtime', 'lib', 'node_modules', 'build', 'build-baseline', 'source'}
GENERATED = {'docs/review/inventory.md', 'docs/review/inventory.json',
             'docs/review/workspace-inventory.md', 'docs/review/workspace-inventory.json'}
LINK = re.compile(r'!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+"[^"\n]*")?\s*\)')
REFERENCE = re.compile(r'^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)', re.M)

def documents():
    return sorted(p for p in ROOT.rglob('*') if p.is_file()
                  and p.suffix.lower() in {'.md', '.rst', '.adoc'}
                  and not any(s in SKIP or s.startswith('build-') for s in p.relative_to(ROOT).parts)
                  and p.relative_to(ROOT).as_posix() not in GENERATED)

def missing_links(path, text):
    # Fenced command examples are not prose links.
    prose = re.sub(r'^```[^\n]*\n.*?^```\s*$', '', text, flags=re.M | re.S)
    missing = []
    for match in list(LINK.finditer(prose)) + list(REFERENCE.finditer(prose)):
        target = match.group(1).strip('<>')
        if target.startswith('#') or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
            continue
        filename = unquote(target.split('#', 1)[0].split('?', 1)[0])
        if filename and not (path.parent / filename).exists():
            missing.append({'target': target, 'line': text[:text.find(match.group(0))].count('\n') + 1})
    return missing

def category(rel, text):
    low = text.lower()
    parts = Path(rel).parts
    if rel.startswith('docs/user/'):
        return 'Operator guide', 'Keep', 'CLI/dictionary/configuration sources cited in guide'
    if any(x in parts for x in ('history', 'results', 'evidence', 'measurements', 'legacy-rev-a')):
        return 'Historical evidence', 'Keep as evidence', 'Recorded configuration only; no fresh hardware validation'
    if re.search(r'(historical reference|archived in place|historical installed-profile|>\s*\*\*historical|\*\*superseded)', low[:900]):
        return 'Historical design', 'Keep as history', 'Do not use as current procedure'
    if rel.startswith('docs/architecture/operations/'):
        return 'Proposed operations', 'Keep as draft', 'Mission intent; bench implementation is separate'
    if rel.startswith(('docs/research/', 'hardware/component_datasheets', 'hardware/hardware_vendors')):
        return 'Research reference', 'Keep as reference', 'External sources not revalidated'
    if 'todo' in Path(rel).name.lower():
        return 'Work checklist', 'Keep', 'Owning workstream; checked items are dated evidence'
    if len(text.splitlines()) <= 15:
        return 'Navigation or placeholder', 'Keep', 'Preserve navigation; empty planning folders are not implemented features'
    if rel.startswith('hardware/'):
        return 'Hardware design or procedure', 'Retain; engineering review pending', 'Content/link triage only; CAD and electrical limits not requalified'
    if rel.startswith(('analysis/', 'rf/', 'test/')):
        return 'Analysis or validation plan', 'Keep as reference', 'Assumptions and acceptance limits need owning engineering review'
    if rel.startswith('system/integration/'):
        return 'Integration plan', 'Keep as draft', 'Planned coverage is not passing evidence'
    return 'Implementation reference', 'Keep', 'Content/link triage; see findings for verified corrections'

def workspace_inventory(workspace, review_date):
    """Index other copies without editing them or resolving branch differences."""
    result = subprocess.run(['git', '-C', str(ROOT), 'worktree', 'list', '--porcelain'],
                            check=True, text=True, capture_output=True).stdout
    roots = []
    for block in result.strip().split('\n\n'):
        fields = dict(line.split(' ', 1) for line in block.splitlines() if ' ' in line)
        path = Path(fields['worktree'])
        if path.exists():
            roots.append({'path': str(path), 'commit': fields.get('HEAD'),
                          'branch': fields.get('branch', 'detached').removeprefix('refs/heads/'),
                          'is_edit_target': path.resolve() == ROOT.resolve()})
    roots.append({'path': str(workspace), 'branch': None, 'commit': None,
                  'is_edit_target': False, 'scope': 'Loose files and snapshots outside indexed worktrees'})
    entries = []
    artifacts = []
    worktrees = [Path(r['path']).resolve() for r in roots[:-1]]
    for info in roots:
        base = Path(info['path'])
        for path in sorted(base.rglob('*')):
            rel = path.relative_to(base)
            if not path.is_file() or any(s in SKIP or s.startswith('build-') for s in rel.parts):
                continue
            if base == workspace and any(path.resolve().is_relative_to(w) for w in worktrees):
                continue
            if rel.as_posix() in GENERATED:
                continue
            if path.suffix.lower() in {'.pdf', '.docx', '.pptx', '.html', '.mm'}:
                artifacts.append({'path': str(path), 'root': str(base), 'bytes': path.stat().st_size,
                                  'review': 'Metadata inventory only; rendered content not reviewed'})
            if path.suffix.lower() not in {'.md', '.rst', '.adoc'}:
                continue
            body = path.read_text(errors='replace')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            counterpart = ROOT / rel
            comparison = 'No same-path document in edit target'
            if counterpart.is_file():
                comparison = ('Identical to edit target' if digest == hashlib.sha256(counterpart.read_bytes()).hexdigest()
                              else 'Differs from edit target; preserve and reconcile by topic')
            if info['is_edit_target']:
                comparison = 'Reviewed edit target'
            disposition = ('Keep active worktree; do not consolidate by copying' if info.get('branch')
                           else 'Retain snapshot/history outside current navigation')
            if base == workspace and rel.parts[:2] == ('docs', 'operations'):
                disposition = 'Archived in place; pointer to repository draft'
            headings = re.findall(r'^#{1,6}\s+(.+)$', body, flags=re.M)
            entries.append({'path': str(path), 'relative_path': rel.as_posix(), 'root': str(base),
                            'title': headings[0] if headings else path.stem,
                            'sha256': digest, 'comparison': comparison, 'disposition': disposition,
                            'review': 'Duplicate/status/link triage; other worktree engineering content not requalified',
                            'missing_local_links': missing_links(path, body) if path.suffix.lower() == '.md' else [],
                            'unclosed_code_fence': sum(bool(re.match(r'^\s*```', line)) for line in body.splitlines()) % 2 == 1})
    groups = {}
    for e in entries:
        groups.setdefault(e['sha256'], []).append(e['path'])
    duplicates = [group for group in groups.values() if len(group) > 1]
    report = {'review_date': review_date, 'roots': roots, 'documents': entries,
              'identical_content_groups': duplicates, 'other_artifacts': artifacts,
              'limits': 'Working tree snapshot; branches may change independently. No remote or live deployment inspection. Other worktree Markdown, CAD, and artifacts not modified.'}
    (ROOT / 'docs/review/workspace-inventory.json').write_text(json.dumps(report, indent=2) + '\n')
    counts = Counter(e['root'] for e in entries)
    lines = ['# Workspace documentation copies', '', '[Review](README.md) · [Full inventory](workspace-inventory.json)', '',
             f'Read-only snapshot on {review_date}: {len(entries)} Markdown/text documents across {len(roots)} locations, '
             f'{len(duplicates)} identical-content groups, and {len(artifacts)} other document/HTML/mind-map artifacts.', '',
             'This expands the repository audit to loose copies and existing worktrees. Duplicate copies do not establish separate authorities. Differing branch content must be reconciled by topic and evidence; do not overwrite an active checkout. Artifact metadata is inventoried, but rendered contents and external repositories/services are outside this review.', '',
             '| Location | Branch | Commit | Documents | Treatment |', '|---|---|---|---|---|']
    for info in roots:
        lines.append(f"| `{info['path']}` | {info.get('branch') or 'Loose files/snapshots'} | {(info.get('commit') or '')[:8]} | {counts[info['path']]} | {'Current edit target' if info['is_edit_target'] else 'Retain independently'} |")
    lines += ['', '## Differences requiring reconciliation', '',
              'Same-path differences below include this audit’s intentional corrections as well as pre-existing branch work. New documents in another checkout are listed too. The JSON also lists unchanged duplicates, missing links and formatting issues in those unedited copies.', '',
              '| Copy | Comparison |', '|---|---|']
    for e in entries:
        if e['root'] != str(ROOT) and e['comparison'] != 'Identical to edit target':
            lines.append(f"| [{e['path']}](<{e['path']}>) | {e['comparison']} |")
    lines += ['', '## Other artifacts', '',
              '| File | Bytes | Review depth |', '|---|---|---|']
    for a in artifacts:
        lines.append(f"| [{a['path']}](<{a['path']}>) | {a['bytes']} | Metadata only |")
    (ROOT / 'docs/review/workspace-inventory.md').write_text('\n'.join(lines) + '\n')
    print(f'Workspace: {len(entries)} text documents, {len(duplicates)} duplicate groups, {len(artifacts)} other artifacts')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', default=date.today().isoformat())
    parser.add_argument('--check', action='store_true', help='Check links without updating inventory')
    parser.add_argument('--workspace', help='Also inventory this workspace and existing Git worktrees read-only')
    args = parser.parse_args()
    findings_path = ROOT / 'docs/review/findings.json'
    findings = json.loads(findings_path.read_text()) if findings_path.exists() else []
    overrides = {}
    for finding in findings:
        for rel in finding['documents']:
            overrides.setdefault(rel, []).append(finding)
    entries = []
    for path in documents():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(errors='replace')
        kind, disposition, evidence = category(rel, text)
        issues = overrides.get(rel, [])
        if issues:
            disposition = '; '.join(dict.fromkeys(i['disposition'] for i in issues))
            evidence = '; '.join(i['id'] for i in issues)
        missing = missing_links(path, text) if path.suffix.lower() == '.md' else []
        if missing and not issues:
            disposition = 'Update links'
        headings = re.findall(r'^#{1,6}\s+(.+)$', text, flags=re.M)
        status = [line.strip() for line in text.splitlines()
                  if re.search(r'(?:status|historical|superseded|draft|recorded|updated|baseline)', line, re.I)][:3]
        entries.append({'path': rel, 'title': headings[0] if headings else path.stem,
                        'category': kind, 'disposition': disposition, 'review_basis': evidence,
                        'lines': len(text.splitlines()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'status_excerpts': status, 'finding_ids': [i['id'] for i in issues],
                        'missing_local_links': missing,
                        'unclosed_code_fence': sum(bool(re.match(r'^\s*```', line)) for line in text.splitlines()) % 2 == 1})
    broken = [(e['path'], m['target']) for e in entries for m in e['missing_local_links']]
    unclosed = [e['path'] for e in entries if e['unclosed_code_fence']]
    print(f'{len(entries)} documents; {len(broken)} missing local file links; {len(unclosed)} unclosed code fences')
    for rel in unclosed:
        print(f'Unclosed fence: {rel}')
    for rel, target in broken:
        print(f'{rel} -> {target}')
    if args.check:
        raise SystemExit(bool(broken or unclosed))
    report = {'review_date': args.date, 'scope': 'First-party repository documentation; tracked and untracked working tree',
              'limitations': 'Inventory and content triage; code/configuration checks only where cited. No external URL/anchor, CAD, hardware, or live service verification.',
              'counts': dict(Counter(e['category'] for e in entries)), 'documents': entries}
    (ROOT / 'docs/review/inventory.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# Documentation inventory', '', '[Review and findings](README.md)', '',
             f'Review date: {args.date}. {len(entries)} first-party documents in this working tree.', '',
             'Every file has a content classification and local file-link check. Only rows with finding IDs have a specific reviewed correction; other rows are editorial triage, not engineering approval. Generated inventory files and dependencies/builds are excluded.', '',
             'See [machine-readable inventory](inventory.json) for hashes, status excerpts, review basis, and missing links. Paths link to the owning document. Keep evidence at its recorded path; archive superseded records in place with a status notice.', '',
             '| Document | Type | Disposition | Findings |', '|---|---|---|---|']
    for e in entries:
        lines.append(f"| [{e['path']}](../../{e['path']}) | {e['category']} | {e['disposition']} | {', '.join(e['finding_ids']) or 'Content/link triage'} |")
    (ROOT / 'docs/review/inventory.md').write_text('\n'.join(lines) + '\n')
    if args.workspace:
        workspace_inventory(Path(args.workspace).resolve(), args.date)

if __name__ == '__main__':
    main()
