#!/usr/bin/env python3
"""Apply the tlween branding on top of upstream PhotoCraft.

Only user-visible text is rebranded; crate names, file formats and other internals keep their
upstream names so `git merge upstream/main` stays easy. The script is idempotent: after merging
upstream, resolve any conflicts in favour of upstream and run it again.

    python3 studio/rebrand.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = 'tlween'
REPO = 'https://github.com/7mz410/CreativeStudio-tlween'
SITE = 'https://studio.creative.ps'
# Persisted names that saved catalogs and presets refer to; renaming them would break those.
KEEP = ('Default PhotoCraft Size', 'PhotoCraft Studio CMYK', 'the PhotoCraft authors')

# Exact replacements, applied before the general rename (and kept idempotent: skipped once done).
RTL_RULES = [
    ('crates/ui-egui/src/cjk_fonts.rs', """                assert_eq!(stack.iter().filter(|n| n.starts_with(FONT_PREFIX)).count(), 3);
                assert_eq!(stack.last().map(String::as_str), Some("system-cjk-2"), "appended last so Latin keeps Inter");""", """                assert_eq!(stack.iter().filter(|n| n.starts_with(FONT_PREFIX)).count(), 2);
                assert_eq!(stack.last().map(String::as_str), Some("system-cjk-1"), "appended last so Latin keeps Inter");"""),
    ('crates/ui-egui/src/cjk_fonts.rs', """                assert!(p.0.scripts_tried.contains(&Script::Hebrew));
                assert_eq!(p.0.registered.len(), 3);""", """                assert!(p.0.scripts_tried.contains(&Script::Hebrew));
                assert_eq!(p.0.registered.len(), 2); // Creative Studio: Arabic is built in"""),
    # Upstream's tests assume no right-to-left catalog and load Arabic glyphs on demand; ours ships
    # Arabic (right to left) with IBM Plex Sans Arabic built in.
    ('crates/ui-egui/src/direction_tests.rs', """    for lang in Lang::all() {
        assert_eq!(lang.dir(), Dir::Ltr, "{}", lang.code());
    }""", """    for lang in Lang::all() {
        let want = if lang.code() == "ar" { Dir::Rtl } else { Dir::Ltr };
        assert_eq!(lang.dir(), want, "{}", lang.code());
    }"""),
    ('crates/ui-egui/src/cjk_fonts.rs', 'assert_eq!(fallback_files(&ctx), ["thai.ttf", "arabic.ttf", "devanagari.ttf"], "the first file that maps the character, never Inter");',
     'assert_eq!(fallback_files(&ctx), ["thai.ttf", "devanagari.ttf"], "the first file that maps the character, never Inter (Arabic is built in)");'),
    # Arabic is supported now: the 'unsupported language' tests use Hebrew instead.
    ('crates/ui-egui/src/i18n/live_tests.rs', '    for tags in [vec![], vec!["sv-SE", "ar-SA"]] {', '    for tags in [vec![], vec!["sv-SE", "he-IL"]] {'),
    ('crates/ui-egui/src/i18n/system.rs', '            (vec!["sv-SE", "ar-SA"], "en"),', '            (vec!["sv-SE", "he-IL"], "en"),'),
    ('crates/ui-egui/src/i18n/mod.rs', 'fn plural_none(_: u64) -> usize {\n', '/// Creative Studio: Arabic: zero, one, two, few (n % 100 in 3–10), many (n % 100 in 11–99), other.\nfn plural_arabic(n: u64) -> usize {\n    match (n, n % 100) {\n        (0, _) => 0,\n        (1, _) => 1,\n        (2, _) => 2,\n        (_, 3..=10) => 3,\n        (_, 11..=99) => 4,\n        _ => 5,\n    }\n}\n\nfn plural_none(_: u64) -> usize {\n'),
    ('crates/ui-egui/src/i18n/mod.rs', '    LangInfo { code: "uk", name: "Українська", source: catalog!("uk"), plural: plural_russian, complete_menus: true, catalog: OnceLock::new() },\n', '    LangInfo { code: "uk", name: "Українська", source: catalog!("uk"), plural: plural_russian, complete_menus: true, catalog: OnceLock::new() },\n    // Creative Studio: Arabic (studio/ar-work), right to left.\n    LangInfo { code: "ar", name: "العربية", source: catalog!("ar"), plural: plural_arabic, complete_menus: true, catalog: OnceLock::new() },\n'),
    # Upstream's README moved to docs/UPSTREAM-README.md (ours is the fork's).
    ('crates/ui-egui/src/state.rs', '        let readme = include_str!("../../../README.md");', '        let readme = include_str!("../../../docs/UPSTREAM-README.md");'),
    ('Cargo.toml', '[workspace.dependencies]', '[patch.crates-io]\n# Creative Studio: egui with a right-to-left switch for the Arabic interface (studio/RTL.md).\negui = { path = "vendor/egui" }\n\n[workspace.dependencies]'),
    ('crates/ui-egui/src/i18n/mod.rs', 'mod catalog;\n', '/// Creative Studio: Arabic in visual order for egui.\npub(crate) mod bidi;\nmod catalog;\n'),
    ('crates/ui-egui/src/i18n/mod.rs', '        self.catalog.get_or_init(|| Catalog::parse(&self.text()))', '        // Creative Studio: right-to-left catalogs are stored in visual order (bidi.rs).\n        self.catalog.get_or_init(|| if bidi::RTL_CODES.contains(&self.code) { Catalog::parse(&bidi::visual_catalog(&self.text())) } else { Catalog::parse(&self.text()) })'),
    ('crates/ui-egui/src/lib.rs', '        let ctx = ui.ctx().clone();\n        i18n::set_current(i18n::Lang::from_pref(&self.session.prefs().interface.language));\n', '        let ctx = ui.ctx().clone();\n        i18n::set_current(i18n::Lang::from_pref(&self.session.prefs().interface.language));\n        // Creative Studio: Arabic lays the interface out right to left (vendor/egui). The switch is\n        // process-wide, so unit tests, which run in parallel, leave it off (tests/rtl.rs covers it).\n        #[cfg(not(test))]\n        egui::set_rtl(i18n::bidi::RTL_CODES.contains(&i18n::current().code()));\n'),
    ('crates/ui-egui/src/panels.rs', 'egui::Panel::left("toolbar")', '(if egui::is_rtl() { egui::Panel::right("toolbar") } else { egui::Panel::left("toolbar") })'),
    ('crates/ui-egui/src/panels.rs', 'egui::Panel::right("rail")', '(if egui::is_rtl() { egui::Panel::left("rail") } else { egui::Panel::right("rail") })'),
    ('crates/ui-egui/src/panels.rs', 'let mut panel = egui::Panel::right("dock")', 'let mut panel = (if egui::is_rtl() { egui::Panel::left("dock") } else { egui::Panel::right("dock") })'),
    ('crates/ui-egui/src/theme.rs', '    // Named weights fall back to the default stack for missing glyphs.\n', '    // Creative Studio: Arabic glyphs (IBM Plex Sans Arabic, OFL) after the default stack.\n    if let Some(arabic) = add(&mut fonts, "Plex Arabic", include_bytes!("../../../assets/fonts/IBMPlexSansArabic-Regular.ttf")) {\n        fonts.families.entry(FontFamily::Proportional).or_default().push(arabic);\n    }\n    // Named weights fall back to the default stack for missing glyphs.\n'),
]

SPECIFIC = {
    # No Creative Studio Discord yet: drop upstream's community button and the ArtCraft website link.
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
        ('assert_eq!(has_discord, width > 1000.0, "Discord at {width}");', 'assert!(!has_discord, "Creative Studio: no Discord button ({width})");'),
    ],
    'crates/ui-egui/src/links.rs': [
        ('pub const APP_PAGE: &str = "https://getartcraft.com/apps/photocraft";', f'pub const APP_PAGE: &str = "{SITE}";'),
        ('pub const GITHUB: &str = "https://github.com/storytold/photocraft";', f'pub const GITHUB: &str = "{REPO}";'),
        ('    let links = [(tl!("PhotoCraft website"), APP_PAGE), (tl!("GitHub"), GITHUB), (tl!("ArtCraft"), ARTCRAFT_WEBSITE)];',
         '    let links = [(tl!("Creative Studio Website"), APP_PAGE), (tl!("GitHub"), GITHUB)];'),
        ('pub const ISSUES: &str = "https://github.com/storytold/photocraft/issues";', f'pub const ISSUES: &str = "{REPO}/issues";'),
        ('            ("help.website", "https://getartcraft.com/apps/photocraft"),\n            ("help.github", "https://github.com/storytold/photocraft"),',
         f'            ("help.website", "{SITE}"),\n            ("help.github", "{REPO}"),'),
    ],
}
# Exact replacements inside string literals and catalogs, before the general rename.
LITERALS = [
    ('Join the ArtCraft Discord', 'Upstream Community on Discord'),
    ('Join the ArtCraft community on Discord', 'The upstream ArtCraft community on Discord'),
    ('ArtCraft Website', 'Creative Studio Website'),
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
    out = out.replace('<string>ai.storyteller.photocraft</string>', '<string>ps.creative.studio.tlween</string>')
    if out != src:
        path.write_text(out, encoding='utf-8')
    return out != src


def RUST_FILES():
    # Creative Studio: the Help menu labels come from the engine's shell command table.
    return sorted((ROOT / 'crates/ui-egui/src').rglob('*.rs')) + sorted((ROOT / 'apps/photocraft/src').rglob('*.rs')) + [ROOT / 'crates/engine/src/shell_commands.rs']


def apply_rtl_rules() -> list:
    changed = []
    for rel, a, b in RTL_RULES:
        path = ROOT / rel
        src = path.read_text(encoding='utf-8')
        if (not b or b not in src) and a in src:
            path.write_text(src.replace(a, b), encoding='utf-8')
            changed.append(path)
    return changed


def fix_language_count() -> list:
    # The table's length follows its rows (upstream adds languages; we add Arabic).
    p = ROOT / 'crates/ui-egui/src/i18n/mod.rs'
    s = p.read_text(encoding='utf-8')
    m = re.search(r'pub static LANGUAGES: \[LangInfo; (\d+)\] = \[(.*?)\n\];', s, re.S)
    if not m:
        return []
    n = len(re.findall(r'LangInfo \{', m.group(2)))
    if int(m.group(1)) == n:
        return []
    p.write_text(s[:m.start(1)] + str(n) + s[m.end(1):], encoding='utf-8')
    return [p]


def main():
    changed = apply_rtl_rules()
    changed += fix_language_count()
    changed += [p for p in RUST_FILES() if rebrand_rust(p)]
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


# Creative Studio: the macOS app folder in the .dmg and the volume name carry our name
# (packaging/macos/package.sh). Bundle and binary names inside the package stay as upstream has them.
PACKAGING_NAMES = {
    'packaging/macos/package.sh': [
        ('PhotoCraft.app', 'tlween.app'),
        ('-volname "PhotoCraft"', '-volname "tlween"'),
        ('-hfs-volume-name "PhotoCraft"', '-hfs-volume-name "tlween"'),
    ],
}


def apply_packaging_names() -> list:
    changed = []
    for rel, pairs in PACKAGING_NAMES.items():
        path = ROOT / rel
        src = path.read_text(encoding='utf-8')
        out = src
        for a, b in pairs:
            out = out.replace(a, b)
        if out != src:
            path.write_text(out, encoding='utf-8')
            changed.append(path)
    return changed


# Creative Studio: documents save as `.tlween` (the same contents as `.pcraft`, which still opens).
# Each pair is applied once: skipped when its new text is already there, so a second run changes
# nothing. Only the save/open surface changes; `.pcraft` reading and internal ids stay upstream's.
EXT_RULES = {
    'crates/format/src/lib.rs': [
        ('pub const EXTENSION: &str = "pcraft";\n',
         'pub const EXTENSION: &str = "pcraft";\n'
         '/// tlween saves documents as `.tlween` (the same contents as `.pcraft`, which still opens).\n'
         'pub const STUDIO_EXTENSION: &str = "tlween";\n'),
    ],
    'crates/io/src/lib.rs': [
        ('    if has_extension(name, photocraft_format::EXTENSION) || photocraft_format::is_pcraft(bytes) {',
         '    if has_extension(name, photocraft_format::EXTENSION) || has_extension(name, photocraft_format::STUDIO_EXTENSION) || photocraft_format::is_pcraft(bytes) {'),
        ('    if ext == photocraft_format::EXTENSION {\n        let doc = named_for_file(doc, name_or_ext);',
         '    if ext == photocraft_format::EXTENSION || ext == photocraft_format::STUDIO_EXTENSION {\n        let doc = named_for_file(doc, name_or_ext);'),
    ],
    'crates/automation/src/files.rs': [
        ('is_some_and(|extension| extension.eq_ignore_ascii_case(photocraft_format::EXTENSION)) {',
         'is_some_and(|extension| extension.eq_ignore_ascii_case(photocraft_format::EXTENSION) || extension.eq_ignore_ascii_case(photocraft_format::STUDIO_EXTENSION)) {'),
        ('    if ext == photocraft_format::EXTENSION {\n        let named = named_for_output(doc, &path.to_string_lossy());',
         '    if ext == photocraft_format::EXTENSION || ext == photocraft_format::STUDIO_EXTENSION {\n        let named = named_for_output(doc, &path.to_string_lossy());'),
        ('    if ext == photocraft_format::EXTENSION {\n        let named = named_for_output(doc, name);',
         '    if ext == photocraft_format::EXTENSION || ext == photocraft_format::STUDIO_EXTENSION {\n        let named = named_for_output(doc, name);'),
    ],
    'crates/engine/src/file_cmds.rs': [
        ('"psb", "pcraft", "png", "jpg"', '"psb", "pcraft", "tlween", "png", "jpg"'),
        ('matches!(ext, "psd" | "psb" | "pcraft" | "ora")', 'matches!(ext, "psd" | "psb" | "pcraft" | "tlween" | "ora")'),
        ('        "psd" | "psb" | "pcraft" => true,', '        "psd" | "psb" | "pcraft" | "tlween" => true,'),
    ],
    'crates/engine/src/print_cmds.rs': [
        ('Some(f @ ("psd" | "psb" | "pcraft")) => f.to_string(),', 'Some(f @ ("psd" | "psb" | "pcraft" | "tlween")) => f.to_string(),'),
        ('(pcraft|psd|psb)"', '(tlween|pcraft|psd|psb)"'),
        ('        None => "pcraft".into(),', '        None => "tlween".into(),'),
        ('"format":"pcraft|psd|psb"="pcraft"', '"format":"tlween|pcraft|psd|psb"="tlween"'),
    ],
    'crates/ui-egui/src/file_dialog/tests.rs': [
        ('"/pics/layers.pcraft"', '"/pics/layers.tlween"'),
        ('"/pics/My image.psd"', '"/pics/My image.tlween"'),
        ('"My image.psd"', '"My image.tlween"'),
        ('("/pics/My image.pcraft", true),', '("/pics/My image.tlween", true),'),
        ('"/pics/transparent.psd"', '"/pics/transparent.tlween"'),
        ('suggested.ends_with(".psd")', 'suggested.ends_with(".tlween")'),
        ('assert_eq!(*written.borrow(), ["/pics/cat.psd"]);\n    assert_eq!(app.session.active().unwrap().path.as_deref(), Some("/pics/cat.psd"));',
         'assert_eq!(*written.borrow(), ["/pics/cat.tlween"]);\n    assert_eq!(app.session.active().unwrap().path.as_deref(), Some("/pics/cat.tlween"));'),
        ('suggested == "/pics/art.psd"), "Save As offers PSD");', 'suggested == "/pics/art.tlween"), "Save As offers tlween");'),
        ('assert_eq!(*written.borrow(), ["/pics/cat.psd", "/pics/dog.png"]);', 'assert_eq!(*written.borrow(), ["/pics/cat.tlween", "/pics/dog.png"]);'),
    ],
    'crates/ui-egui/src/file_open/tests.rs': [
        ('suggested: "Untitled-2.psd".into()', 'suggested: "Untitled-2.tlween".into()'),
    ],
    'crates/engine/src/print_cmds/tests.rs': [
        ('assert!(docp.ends_with("Print Me/Print Me.pcraft"));', 'assert!(docp.ends_with("Print Me/Print Me.tlween"));'),
        ('photocraft_io::import("Print Me.pcraft"', 'photocraft_io::import("Print Me.tlween"'),
    ],
    'crates/engine/src/video_cmds.rs': [
        ('"exr" | "pcraft" | "psd")', '"exr" | "pcraft" | "tlween" | "psd")'),
    ],
    'crates/ui-egui/src/lib.rs': [
        ('matches!(e.as_str(), photocraft_format::EXTENSION | "psd" | "psb" | "tif" | "tiff")',
         'matches!(e.as_str(), photocraft_format::EXTENSION | photocraft_format::STUDIO_EXTENSION | "psd" | "psb" | "tif" | "tiff")'),
        ('            Some(p) if writable => p.clone(),',
         '            Some(p) if writable && std::path::Path::new(p).extension().is_some_and(|e| e.eq_ignore_ascii_case("pcraft")) => std::path::Path::new(p).with_extension("tlween").to_string_lossy().into_owned(),\n'
         '            Some(p) if writable => p.clone(),'),
        ('                    Some("pdn") => "pcraft",', '                    Some("pdn") => "tlween",'),
        ('                    _ => "psd",\n                };', '                    _ => "tlween",\n                };'),
    ],
    'crates/ui-egui/src/control.rs': [
        ('.is_some_and(|(_, ext)| ext.eq_ignore_ascii_case(photocraft_format::EXTENSION))',
         '.is_some_and(|(_, ext)| ext.eq_ignore_ascii_case(photocraft_format::EXTENSION) || ext.eq_ignore_ascii_case(photocraft_format::STUDIO_EXTENSION))'),
    ],
    'apps/photocraft/src/services.rs': [
        ('    "pcraft", "pdn", "ora", "kra"', '    "pcraft", "tlween", "pdn", "ora", "kra"'),
        ('        ("All Formats", open_filter_extensions(OPEN_EXTS)),\n        ("tlween", open_filter_extensions(&["pcraft"])),',
         '        ("tlween", open_filter_extensions(&["tlween", "pcraft"])),\n        ("All Formats", open_filter_extensions(OPEN_EXTS)),'),
        ('"pcraft jpeg gif bmp psd",', '"tlween jpeg gif bmp tlween",'),
        ('"psd",                       // Save As untitled', '"tlween",                     // Save As untitled'),
        ('assert_eq!(save_filters("Untitled")[0].0, "PSD Document", "no extension keeps the default");', 'assert_eq!(save_filters("Untitled")[0].0, "tlween", "no extension keeps the default");'),
        ('let layered = ["psd", "psb", "pcraft", "ora", "pdf"];', 'let layered = ["psd", "psb", "pcraft", "tlween", "ora", "pdf"];'),
        ('    ("PSD Document", &["psd", "psb"]),\n    ("PDF", &["pdf"]),\n    ("tlween", &["pcraft"]),\n',
         '    ("tlween", &["tlween", "pcraft"]),\n    ("PSD Document", &["psd", "psb"]),\n    ("PDF", &["pdf"]),\n'),
    ],
    'apps/photocraft-web/src/web.rs': [
        ('    "pcraft", "pdn", "ora", "kra"', '    "pcraft", "tlween", "pdn", "ora", "kra"'),
    ],
    'packaging/macos/Info.plist.in': [
        ('<string>PhotoCraft Document</string>', '<string>tlween Document</string>'),
        ('<array><string>pcraft</string></array>', '<array><string>tlween</string><string>pcraft</string></array>'),
    ],
    'packaging/linux/ai.storyteller.photocraft.mime.xml': [
        ('<glob pattern="*.pcraft"/>', '<glob pattern="*.pcraft"/>\n    <glob pattern="*.tlween"/>'),
    ],
    'packaging/windows/photocraft.wxs': [
        ('Description="PhotoCraft Document" Icon="PhotocraftExe"', 'Description="tlween Document" Icon="PhotocraftExe"'),
        ('          <Extension Id="pcraft" ContentType="application/x-photocraft">',
         '          <Extension Id="tlween" ContentType="application/x-photocraft">\n'
         '            <Verb Id="open" Command="Open" TargetFile="PhotocraftExe" Argument="&quot;%1&quot;" />\n'
         '          </Extension>\n'
         '          <Extension Id="pcraft" ContentType="application/x-photocraft">'),
        (r'<RegistryValue Root="HKLM" Key="Software\Classes\Applications\photocraft.exe\SupportedTypes" Name=".pcraft" Value="" Type="string" />',
         r'<RegistryValue Root="HKLM" Key="Software\Classes\Applications\photocraft.exe\SupportedTypes" Name=".tlween" Value="" Type="string" />'
         '\n        '
         r'<RegistryValue Root="HKLM" Key="Software\Classes\Applications\photocraft.exe\SupportedTypes" Name=".pcraft" Value="" Type="string" />'),
    ],
}


def apply_extension_rules() -> list:
    changed = []
    for rel, pairs in EXT_RULES.items():
        path = ROOT / rel
        src = path.read_text(encoding='utf-8')
        out = src
        for a, b in pairs:
            if b in out or a not in out:
                continue
            out = out.replace(a, b)
        if out != src:
            path.write_text(out, encoding='utf-8')
            changed.append(path)
    return changed


if __name__ == '__main__':
    main()
    for _p in apply_packaging_names():
        print('rebranded', _p.relative_to(ROOT))
    for _p in apply_extension_rules():
        print('rebranded', _p.relative_to(ROOT))


# Creative Studio: the app's Arabic name in its Arabic interface (studio/arabic_names.py).
import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import arabic_names  # noqa: E402
for _p in arabic_names.apply(ROOT, NAME, "تلوين"):
    print("rebranded", _p.relative_to(ROOT))
