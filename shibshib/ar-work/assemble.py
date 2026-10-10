#!/usr/bin/env python3
"""Build tlween's Arabic catalog (crates/ui-egui/src/i18n/ar.tsv) from the translated batches.

`part_NN` lines are `context<TAB>English` (as in fr.tsv); `tr_NN` holds one translation per line in
the same order, with catalog escapes (\\n). Plural rows take Arabic's six forms
`zero|one|two|few|many|other`.

    python3 shibshib/ar-work/assemble.py
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent.parent / 'crates/ui-egui/src/i18n/ar.tsv'
PH = re.compile(r'\{[^{}]*\}')
HEADER = """# Arabic (ar) catalog. Columns, separated by a TAB:  context <TAB> source <TAB> translation
# (see fr.tsv for the format). @plural rows list Arabic's six forms zero|one|two|few|many|other.
# Translations are written in logical order; i18n/bidi.rs puts them in visual order on load.
#
# Clean-room: every entry was written from the plain meaning of the English label using ordinary
# Arabic computing and design vocabulary. No proprietary localisation resource, string table or
# product UI was consulted or copied; in particular not any Arabic localisation of Adobe Photoshop.
# Made by the ShibShib project (shibshib/ar-work).
"""
rows, problems, done = [], [], 0
for part in sorted(HERE.glob('part_*')):
    tr = HERE / part.name.replace('part_', 'tr_')
    if not tr.exists():
        continue
    keys = part.read_text(encoding='utf-8').rstrip('\n').split('\n')
    vals = tr.read_text(encoding='utf-8').rstrip('\n').split('\n')
    if len(keys) != len(vals):
        problems.append(f'{part.name}: {len(keys)} keys, {len(vals)} translations')
        continue
    for k, v in zip(keys, vals):
        ctx, src = k.split('\t', 1)
        v = src[:len(src) - len(src.lstrip(' '))] + v.strip(' ') + src[len(src.rstrip(' ')):]
        if set(PH.findall(src)) != set(PH.findall(v)):
            problems.append(f'{part.name}: placeholders differ: {src!r} -> {v!r}')
        if ctx == '@plural' and v.count('|') != 5:
            problems.append(f'{part.name}: plural needs 6 forms: {v!r}')
        rows.append(f'{ctx}\t{src}\t{v}')
        done += 1
OUT.write_text(HEADER + '\n'.join(rows) + '\n', encoding='utf-8')
print(f'{done} rows -> {OUT.name}')
for p in problems:
    print('problem:', p)
