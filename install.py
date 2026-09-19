#!/usr/bin/env python3
"""Install the skill, preserving existing files and optional standing instructions."""
import argparse
import datetime
import os
from pathlib import Path
import shutil

START = '<!-- codex-usage-budget:start -->'
END = '<!-- codex-usage-budget:end -->'

def install(home, always=False):
    home = Path(home).expanduser().resolve()
    source = Path(__file__).resolve().parent / 'skill'
    target = home / 'skills' / 'codex-usage-budget'
    if target.is_symlink():
        raise ValueError('Refusing to replace a symlinked skill directory.')
    agents = home / 'AGENTS.md'
    existing = agents.read_text() if agents.exists() else ''
    if always and (START in existing or END in existing):
        if existing.count(START) != 1 or existing.count(END) != 1 or existing.index(END) < existing.index(START):
            raise ValueError('Malformed existing managed instruction block; nothing changed.')
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        backup = home / 'usage-budget-backups' / stamp / 'codex-usage-budget'
        backup.parent.mkdir(parents=True)
        shutil.move(str(target), str(backup))
        print(f'Previous skill backed up to {backup}')
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    if always:
        block = f'''{START}
Before each task, apply the codex-usage-budget skill at `{target / 'SKILL.md'}`.
Reuse a valid project plan or budget the complete deliverable, usage, active hours,
acceptance evidence and stop limits using the least-expensive-good-enough route.
Bounded delegation to an available economical model is authorized for independent
work. Skip additional planning/delegation when its overhead is at least the direct
task cost; retain required verification. Avoid recursive planners and duplicate work.
At ceilings preserve results and replan. Batch usage logging, preserve owner reviews,
and retain pending local data if cloud logging is unavailable. Do not invent quota
conversions or buy credits. This is an instruction, not an enforced spending cap.
{END}'''
        if START in existing:
            before, rest = existing.split(START, 1)
            _, after = rest.split(END, 1)
            updated = before + block + after
        else:
            updated = existing.rstrip() + ('\n\n' if existing.strip() else '') + block + '\n'
        if agents.exists() and updated != existing:
            backup = home / 'usage-budget-backups' / stamp / 'AGENTS.md'
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(agents, backup)
        agents.write_text(updated)
    print(f'Installed {target}')
    print('Start a new Codex task to load the installed skill.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-home', default=os.environ.get('CODEX_HOME', '~/.codex'))
    parser.add_argument('--always', action='store_true', help='Add standing instructions to AGENTS.md (opt-in).')
    args = parser.parse_args()
    install(args.codex_home, args.always)
