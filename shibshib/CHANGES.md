# ShibShib tlween: changes from upstream PhotoCraft

Required by the Apache License 2.0 (section 4b): files we changed carry this notice through
this list.

- Branding (user-visible only, applied by `shibshib/rebrand.py`): the app name ShibShib tlween,
  the bundle id `com.shibshib.tlween`, Help links to shibshib.art and this repository. Crate names
  and file formats keep their upstream names.
- App icon: the ShibShib tlween tile (`assets/app-icon/`).
- Removed upstream's ArtCraft brand assets (`docs/brand/`), as their brand terms require of forks.
- README and NOTICE: the fork, its credits and the ShibShib suite.
- Right-to-left interface for Arabic: the patched egui from ShibShib rsm in `vendor/egui`
  (`shibshib/RTL.md`); the tool bar, rail and dock change sides; `crates/ui-egui/tests/rtl.rs`.
- Arabic groundwork: IBM Plex Sans Arabic (OFL) as the Arabic UI font and
  `crates/ui-egui/src/i18n/bidi.rs` (Arabic catalogs in visual order for egui).
