# tlween: changes from upstream PhotoCraft

Required by the Apache License 2.0 (section 4b): files we changed carry this notice through
this list.

- Branding (user-visible only, applied by `studio/rebrand.py`): the app name tlween,
  the bundle id `ps.creative.studio.tlween`, Help links to studio.creative.ps and this repository. Crate names
  and file formats keep their upstream names.
- App icon: the tlween tile (`assets/app-icon/`).
- Removed upstream's ArtCraft brand assets (`docs/brand/`), as their brand terms require of forks.
- README and NOTICE: the fork, its credits and the Creative Studio suite.
- Right-to-left interface for Arabic: the patched egui from Creative Studio rsm in `vendor/egui`
  (`studio/RTL.md`); the tool bar, rail and dock change sides; `crates/ui-egui/tests/rtl.rs`.
- Arabic groundwork: IBM Plex Sans Arabic (OFL) as the Arabic UI font and
  `crates/ui-egui/src/i18n/bidi.rs` (Arabic catalogs in visual order for egui).
- Arabic interface: `crates/ui-egui/src/i18n/ar.tsv` (2766 entries, built from `studio/ar-work/`),
  Arabic plural rules, in the language list. The "unsupported language" tests use Hebrew now.
