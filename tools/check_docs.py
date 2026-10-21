#!/usr/bin/env python3
"""Check repository-local Markdown links and obvious accidental private artifacts."""
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
failures = []
for file in ROOT.rglob('*.md'):
    if '.git' in file.parts:
        continue
    text = file.read_text(encoding='utf-8')
    for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', text):
        target = target.split('#', 1)[0]
        if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
            continue
        path = (file.parent / unquote(target)).resolve()
        if not path.is_relative_to(ROOT) or not path.exists():
            failures.append(f'{file.relative_to(ROOT)}: missing or out-of-tree link {target}')
for file in ROOT.rglob('*'):
    if not file.is_file() or '.git' in file.parts or '__pycache__' in file.parts:
        continue
    if file.suffix in {'.db','.sqlite','.log'} or file.name == 'auth.json':
        failures.append(f'Private artifact must not be published: {file.relative_to(ROOT)}')
if failures:
    raise SystemExit('\n'.join(failures))
print('Documentation links and private-artifact checks passed.')
