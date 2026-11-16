#!/usr/bin/env python3
"""Run three adaptive design conversations and publish a dated dialogue-only HTML."""
import argparse
import concurrent.futures
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
import time
from zoneinfo import ZoneInfo

from compare import render
import simulator

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'evals/results'
PROTOCOL = 'adaptive-conversations-v1'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def snapshot(ref=None):
    if ref:
        names = git('ls-tree', '-r', '--name-only', ref).splitlines()
    else:
        names = [str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()]
    names = sorted(n for n in names if n == 'SKILL.md' or n.startswith(('references/', 'agents/')))
    return {n: subprocess.check_output(['git', 'show', f'{ref}:{n}'], cwd=ROOT).decode()
            if ref else (ROOT / n).read_text() for n in names}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def write_files(root, files):
    for name, content in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')


def visible_files(work):
    return {str(p.relative_to(work)): p.read_text(errors='replace') for p in work.rglob('*')
            if p.is_file() and '.agents' not in p.relative_to(work).parts}


def call_codex(prompt, work, prefix, timeout, model=None, schema=None):
    prefix.parent.mkdir(parents=True, exist_ok=True)
    Path(str(prefix) + '.prompt.txt').write_text(prompt, encoding='utf-8')
    command = ['codex', 'exec', '--ignore-user-config', '--ephemeral',
               '--disable', 'hooks', '--disable', 'plugins', '--disable', 'apps',
               '--enable', 'skip_host_skill_discovery',
               '--sandbox', 'read-only' if schema else 'workspace-write',
               '-c', 'approval_policy="never"', '--skip-git-repo-check',
               '--json', '--color', 'never', '-C', str(work),
               '-o', str(prefix) + '.reply.txt']
    if model:
        command += ['--model', model]
    if schema:
        schema_path = Path(str(prefix) + '.schema.json')
        save_json(schema_path, schema)
        command += ['--output-schema', str(schema_path)]
    command.append('-')
    start = time.monotonic()
    with Path(str(prefix) + '.events.jsonl').open('w') as stdout, \
            Path(str(prefix) + '.stderr.txt').open('w') as stderr:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout,
                                stderr=stderr, text=True, start_new_session=True)
        status = 'completed'
        try:
            proc.communicate(prompt, timeout=timeout)
            if proc.returncode:
                status = 'error'
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            status = 'timeout'
    reply_path = Path(str(prefix) + '.reply.txt')
    reply = reply_path.read_text() if reply_path.exists() else ''
    events = []
    for line in Path(str(prefix) + '.events.jsonl').read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    if not reply.strip() and status == 'completed':
        status = 'error'
    result = dict(reply=reply, status=status, seconds=round(time.monotonic() - start, 1),
                  messages=[e['item']['text'] for e in events
                            if e.get('type') == 'item.completed'
                            and e.get('item', {}).get('type') == 'agent_message'],
                  usage=[e.get('usage') for e in events if e.get('type') == 'turn.completed'])
    save_json(Path(str(prefix) + '.result.json'), result)
    return result


def execute_case(label, skill, case, out, timeout, model=None):
    # Older snapshots keep their original name when used as a comparison baseline.
    skill_name = re.search(r'^name:\s*([a-z0-9-]+)\s*$',
                           skill['SKILL.md'].split('---', 2)[1], re.MULTILINE).group(1)
    skill_path = f'.agents/skills/{skill_name}'
    target = out / label / case['id']
    target.mkdir(parents=True)
    history, rows, user_runs = [], [], []
    termination = 'turn_limit'
    with tempfile.TemporaryDirectory(prefix='talk-to-plan-assistant-') as tmp, \
            tempfile.TemporaryDirectory(prefix='talk-to-plan-user-') as user_tmp:
        work, user_work = Path(tmp), Path(user_tmp)
        write_files(work / skill_path, skill)
        write_files(work, case['files'])
        for number in range(1, case['max_turns'] + 1):
            done = False
            if number == 1:
                user = case['opening']
            else:
                # Only the simulator sees the persona. It never receives the skill, version,
                # coverage notes, file changes, or a desired assistant response.
                generated = call_codex(simulator.prompt(case, history, number), user_work,
                                       target / f'user-{number}', timeout, model, simulator.SCHEMA)
                user_runs.append(generated)
                try:
                    value = json.loads(generated['reply'])
                    if generated['status'] != 'completed' or not isinstance(value['message'], str) or \
                            not value['message'].strip() or type(value['done']) is not bool:
                        raise ValueError('Invalid simulated user output')
                    user = value['message'].strip()
                    done = value['done'] and number >= case['min_turns']
                except (ValueError, KeyError, TypeError):
                    termination = 'simulator_error'
                    print(f'{label}/{case["id"]}: simulator error at turn {number}', flush=True)
                    break
            history.append({'role': 'user', 'content': user})
            before = visible_files(work)
            prompt = (
                f'使用 ${skill_name}，读取当前目录 {skill_path}/SKILL.md，'
                '按其中的规则继续下面的设计讨论。只使用这个副本，不加载其他位置的同名 skill。\n'
                '当前目录就是这个项目；如需设计文档，使用 DESIGN.md。'
                '无需联网或读取当前目录之外的文件；不要修改 skill 文件。\n'
                '请直接回应最后一条用户消息，并按实际需要使用文件工具。'
                '不要写评测分析，不模拟未来的用户回复。下面的历史是对话记录。\n\n'
                f'项目背景：{case["context"]}\n\n'
                '实际对话：\n' + json.dumps(history, ensure_ascii=False)
            )
            reply = call_codex(prompt, work, target / f'assistant-{number}', timeout, model)
            after = visible_files(work)
            changed = [n for n in sorted(set(before) | set(after)) if before.get(n) != after.get(n)]
            diff = '\n'.join(''.join(difflib.unified_diff(
                before.get(n, '').splitlines(True), after.get(n, '').splitlines(True),
                fromfile='before/' + n, tofile='after/' + n)) for n in changed)
            row = dict(reply, turn=number, user=user, changed=changed, diff=diff,
                       before=before, after=after)
            rows.append(row)
            history.append({'role': 'assistant', 'content': reply['reply']})
            save_json(target / 'conversation.json', rows)
            print(f'{label}/{case["id"]}/{number}: {reply["status"]}', flush=True)
            if reply['status'] != 'completed':
                termination = 'assistant_error'
                break
            if done:
                termination = 'user_done'
                break
    result = dict(variant=label, case=case['id'], rows=rows,
                  termination=termination, simulator_runs=user_runs,
                  completed=termination in ('user_done', 'turn_limit') and bool(rows))
    save_json(target / 'result.json', result)
    return result


def load_snapshots(run):
    path = run / 'snapshots.json'
    if path.exists():
        return read_json(path)
    # Read the original format without producing discoverable nested SKILL.md files.
    return {label: {str(p.relative_to(run / 'snapshots' / label)): p.read_text()
                    for p in (run / 'snapshots' / label).rglob('*') if p.is_file()}
            for label in ('baseline', 'candidate')}


def compatible(previous, cases, engine_hash, model):
    meta = read_json(previous / 'metadata.json')
    if meta.get('protocol') != PROTOCOL or meta.get('engine_hash') != engine_hash or meta.get('model') != model:
        return False
    old_cases = {c['id']: c for c in read_json(previous / 'cases.json')}
    old_results = {r['case']: r for r in read_json(previous / 'results.json') if r['variant'] == 'candidate'}
    return all(old_cases.get(c['id']) == c and old_results.get(c['id'], {}).get('completed')
               for c in cases)


def publish(out, cases, results, meta):
    # Date in Asia/Shanghai; original runs retain their own dated HTML and raw data.
    target = render(out, cases, results, filename=meta['date'] + '.html')
    html_dir = RESULTS / 'html'
    html_dir.mkdir(parents=True, exist_ok=True)
    destination = html_dir / target.name
    pending = html_dir / ('.' + target.name + '.tmp')
    shutil.copyfile(target, pending)
    pending.replace(destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--baseline', help='Rerun both versions, using this commit/tag as baseline')
    source.add_argument('--previous', type=Path, help='Use this previous candidate version/results')
    parser.add_argument('--render-only', type=Path, help='Render a saved adaptive run without model calls')
    parser.add_argument('--cases', nargs='+', help='Run only these conversation IDs')
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--timeout', type=int, default=240, help='Seconds per model call')
    parser.add_argument('--model', help='Use this model for both assistant and simulated user')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.render_only:
        out = args.render_only.resolve()
        meta = read_json(out / 'metadata.json')
        print(publish(out, read_json(out / 'cases.json'), read_json(out / 'results.json'), meta))
        return
    if not shutil.which('codex'):
        parser.error('Codex CLI is required; sign in before running this suite.')
    if args.jobs < 1 or args.timeout < 1:
        parser.error('jobs and timeout must be positive')
    all_cases = read_json(ROOT / 'evals/cases.json')['cases']
    cases = all_cases
    if args.cases:
        unknown = set(args.cases) - {c['id'] for c in cases}
        if unknown:
            parser.error('Unknown cases: ' + ', '.join(sorted(unknown)))
        cases = [c for c in cases if c['id'] in args.cases]
    engine = {name: (ROOT / 'evals' / name).read_text() for name in ('run.py', 'simulator.py')}
    engine_hash = digest(engine)
    model = args.model or 'CLI default (not pinned)'
    latest = RESULTS / 'latest.json'
    previous = args.previous.resolve() if args.previous else None
    if previous is None and not args.baseline and latest.exists():
        previous = Path(read_json(latest)['run'])
    results, head, reuse = [], None, False
    if previous:
        baseline = load_snapshots(previous).get('candidate', {})
        if 'SKILL.md' not in baseline:
            parser.error('Previous run is missing its candidate skill snapshot')
        reuse = compatible(previous, cases, engine_hash, model)
        if reuse:
            results = [dict(r, variant='baseline') for r in read_json(previous / 'results.json')
                       if r['variant'] == 'candidate' and r['case'] in {c['id'] for c in cases}]
        else:
            print('Cases or runner changed: rerunning the previous skill snapshot with the new conversations.', flush=True)
    else:
        head = git('rev-parse', (args.baseline or 'HEAD') + '^{commit}')
        baseline = snapshot(head)
    variants = {'baseline': baseline, 'candidate': snapshot()}
    now = dt.datetime.now(ZoneInfo('Asia/Shanghai'))
    stamp = now.strftime('%Y-%m-%d_%H%M%S_%f')
    out = (args.output or RESULTS / 'runs' / stamp).resolve()
    out.mkdir(parents=True, exist_ok=False)
    meta = dict(protocol=PROTOCOL, baseline=head, previous_run=str(previous) if previous else None,
                baseline_reused=reuse, date=now.strftime('%Y-%m-%d'), created_at=now.isoformat(),
                cli_version=subprocess.check_output(['codex', '--version'], text=True).strip(),
                model=model, engine_hash=engine_hash, cases_hash=digest(cases),
                skill_hashes={k: digest(v) for k, v in variants.items()},
                jobs=args.jobs, timeout=args.timeout,
                isolation='ignore user config; hooks/plugins/apps disabled; host skill discovery skipped',
                completed=False)
    save_json(out / 'metadata.json', meta)
    save_json(out / 'cases.json', cases)
    save_json(out / 'snapshots.json', variants)
    save_json(out / 'engine.json', engine)
    save_json(out / 'results.json', results)
    print('Run directory: ' + str(out), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        jobs = {pool.submit(execute_case, label, files, case, out, args.timeout, args.model):
                (label, case['id']) for case in cases for label, files in variants.items()
                if not (reuse and label == 'baseline')}
        for future in concurrent.futures.as_completed(jobs):
            try:
                result = future.result()
            except Exception as error:
                label, case_id = jobs[future]
                saved = out / label / case_id / 'conversation.json'
                result = dict(variant=label, case=case_id, rows=read_json(saved) if saved.exists() else [],
                              completed=False, termination='runner_error', error=str(error))
                print(f'{label}/{case_id}: runner error: {error}', flush=True)
            results.append(result)
            save_json(out / 'results.json', results)
    meta['completed'] = len(results) == 2 * len(cases) and all(r['completed'] for r in results)
    save_json(out / 'metadata.json', meta)
    destination = publish(out, cases, results, meta)
    if meta['completed'] and cases == all_cases:
        save_json(latest, {'run': str(out), 'html': str(destination)})
    print('HTML: ' + str(destination), flush=True)
    if not meta['completed']:
        raise SystemExit('Some conversations failed; raw logs retained. Latest baseline was not advanced.')


if __name__ == '__main__':
    main()
