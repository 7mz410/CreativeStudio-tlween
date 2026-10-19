//! Creative Studio: a document saves as `.tlween` (the same native contents as `.pcraft`), and a
//! `.pcraft` file still opens. The rules that set this up are in `studio/rebrand.py`.

use photocraft_color::{ColorMode, SampleType};
use photocraft_doc::Document;
use photocraft_format::SaveOptions;
use photocraft_geom::Size;
use photocraft_io::{ExportOptions, export, import};

fn doc() -> Document {
    Document::new("a", Size::new(16, 16), ColorMode::Rgb, SampleType::U8)
}

#[test]
fn a_saved_document_is_a_tlween_file_that_reopens() {
    assert_eq!(photocraft_format::STUDIO_EXTENSION, "tlween");
    let bytes = export(&doc(), "a.tlween", &ExportOptions::default()).expect("export .tlween").bytes;
    assert!(photocraft_format::is_pcraft(&bytes), "a .tlween save writes the native contents");
    let reopened = import("a.tlween", &bytes).expect("a .tlween opens").document;
    assert_eq!(reopened.size, Size::new(16, 16));
}

#[test]
fn a_pcraft_file_still_opens() {
    let bytes = photocraft_format::save_to_bytes(&doc(), &SaveOptions::default()).expect("save");
    let opened = import("old.pcraft", &bytes).expect("a .pcraft file opens").document;
    assert_eq!(opened.size, Size::new(16, 16));
}
