# References

## Supported inputs
- Single images
- Single-page PDFs
- Multi-page PDFs
- Supports multi-page PDF conversion with page-by-page fallback

## Runtime dependencies
- `PyMuPDF` / `fitz`
- `Pillow` / `PIL`
- `PaddleOCR` / `paddleocr`
- `python-pptx` / `pptx`

## Dependency probing
- Use `scripts/dependencies.py` to detect runtime support before enabling optional extraction paths.
- Treat OCR support as optional; missing OCR support must not block fidelity-first PPT output.

## Fallback policy
- Preserve background fidelity first
- Only promote high-confidence text and images
- If OCR is unavailable at runtime, keep scanned content in the background layer and continue rendering the slide.

## Known limits
- Missing or subset font mappings can force a fallback to the background layer
- OCR uncertainty on scanned pages can block editable text promotion
- Complex effects remain in the background layer
- Stage-one runtime upgrade still prioritizes text and image layers over complex vector/effect reconstruction
