#!/usr/bin/env python3
"""Apply the ShibShib tlween branding on top of upstream PhotoCraft.

Only user-visible text is rebranded; crate names, file formats and other internals keep their
upstream names so `git merge upstream/main` stays easy. The script is idempotent: after merging
upstream, resolve any conflicts in favour of upstream and run it again.

    python3 shibshib/rebrand.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = 'ShibShib tlween'
REPO = 'https://github.com/7mz410/ShibShib-tlween'
SITE = 'https://shibshib.art'
# Persisted names that saved catalogs and presets refer to; renaming them would break those.
KEEP = ('Default PhotoCraft Size', 'PhotoCraft Studio CMYK', 'the PhotoCraft authors')

# Exact replacements, applied before the general rename (and kept idempotent: skipped once done).
SPECIFIC = {
    # No ShibShib Discord yet: drop upstream's community button and the ArtCraft website link.
    'crates/ui-egui/src/canvas.rs': [
        ('            crate::links::discord_button(app, ui, 190.0);\n            ui.add_space(10.0);\n', ''),
    ],
    'crates/ui-egui/src/dialogs.rs': [
        ('                crate::links::discord_button(app, ui, 220.0);\n                ui.add_space(8.0);\n', ''),
    ],
    'crates/ui-egui/src/panels.rs': [
        ('                    if ui.available_width() >= DISCORD_ROOM {', '                    if false && ui.available_width() >= DISCORD_ROOM {'),
    ],
    'crates/ui-egui/src/titlebar.rs': [
        ('assert_eq!(has_discord, width > 1000.0, "Discord at {width}");', 'assert!(!has_discord, "ShibShib: no Discord button ({width})");'),
    ],
    'crates/ui-egui/src/links.rs': [
        ('pub const APP_PAGE: &str = "https://getartcraft.com/apps/photocraft";', f'pub const APP_PAGE: &str = "{SITE}";'),
        ('pub const GITHUB: &str = "https://github.com/storytold/photocraft";', f'pub const GITHUB: &str = "{REPO}";'),
        ('    let links = [(tl!("PhotoCraft website"), APP_PAGE), (tl!("GitHub"), GITHUB), (tl!("ArtCraft"), ARTCRAFT_WEBSITE)];',
         '    let links = [(tl!("ShibShib Website"), APP_PAGE), (tl!("GitHub"), GITHUB)];'),
        ('pub const ISSUES: &str = "https://github.com/storytold/photocraft/issues";', f'pub const ISSUES: &str = "{REPO}/issues";'),
        ('            ("help.website", "https://getartcraft.com/apps/photocraft"),\n            ("help.github", "https://github.com/storytold/photocraft"),',
         f'            ("help.website", "{SITE}"),\n            ("help.github", "{REPO}"),'),
    ],
}
# Exact replacements inside string literals and catalogs, before the general rename.
LITERALS = [
    ('Join the ArtCraft Discord', 'Upstream Community on Discord'),
    ('Join the ArtCraft community on Discord', 'The upstream ArtCraft community on Discord'),
    ('ArtCraft Website', 'ShibShib Website'),
]

STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"')


def rename(text: str) -> str:
    for a, b in LITERALS:
        text = text.replace(a, b)
    if any(k in text for k in KEEP):
        return text
    return text.replace('PhotoCraft', NAME)


def rebrand_rust(path: Path) -> bool:
    src = path.read_text(encoding='utf-8')
    out = src
    for a, b in SPECIFIC.get(path.relative_to(ROOT).as_posix(), []):
        if not b or b not in out:
            out = out.replace(a, b)
    out = STRING.sub(lambda m: rename(m.group(0)), out)
    if out != src:
        path.write_text(out, encoding='utf-8')
    return out != src


def rebrand_locale(path: Path) -> bool:
    # Catalog rows are `context<TAB>English<TAB>translation`.
    src = path.read_text(encoding='utf-8')
    rows = []
    for line in src.split('\n'):
        cells = line.split('\t')
        if len(cells) >= 3 and not line.startswith('#'):
            line = '\t'.join([cells[0], *(rename(c) for c in cells[1:])])
        rows.append(line)
    out = '\n'.join(rows)
    if out != src:
        path.write_text(out, encoding='utf-8')
    return out != src


def rebrand_plist(path: Path) -> bool:
    src = path.read_text(encoding='utf-8')
    out = re.sub(r'(<key>CFBundle(?:Display)?Name</key>\s*<string>)PhotoCraft(</string>)', rf'\g<1>{NAME}\2', src)
    out = out.replace('<string>ai.storyteller.photocraft</string>', '<string>com.shibshib.tlween</string>')
    if out != src:
        path.write_text(out, encoding='utf-8')
    return out != src


def RUST_FILES():
    return sorted((ROOT / 'crates/ui-egui/src').rglob('*.rs')) + sorted((ROOT / 'apps/photocraft/src').rglob('*.rs'))


def main():
    changed = [p for p in RUST_FILES() if rebrand_rust(p)]
    changed += [p for p in sorted((ROOT / 'crates/ui-egui/src/i18n').glob('*.tsv')) if rebrand_locale(p)]
    web = ROOT / 'apps/photocraft-web/index.html'
    html = web.read_text(encoding='utf-8')
    branded = html.replace('<title>PhotoCraft</title>', f'<title>{NAME}</title>').replace('Loading PhotoCraft&hellip;', f"Loading {NAME}&hellip;").replace('content="PhotoCraft:', f'content="{NAME}:')
    if branded != html:
        web.write_text(branded, encoding='utf-8')
        changed.append(web)
    plist = ROOT / 'packaging/macos/Info.plist.in'
    if plist.exists() and rebrand_plist(plist):
        changed.append(plist)
    for p in changed:
        print('rebranded', p.relative_to(ROOT))


if __name__ == '__main__':
    main()
