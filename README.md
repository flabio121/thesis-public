# Public Thesis Repository

This repository provides the public thesis PDF and the minimal source files needed to rebuild the public document.

## Thesis PDF

Direct PDF link: [Favian_Tippin_Thesis.pdf](https://raw.githubusercontent.com/flabio121/thesis-public/main/docs/Favian_Tippin_Thesis.pdf)

The QR code in `docs/qr_thesis_pdf.png` and `docs/qr_thesis_pdf.svg` points directly to that PDF URL.

Optional landing page: [https://flabio121.github.io/thesis-public/](https://flabio121.github.io/thesis-public/)

## Included

- Final thesis PDF in `docs/Favian_Tippin_Thesis.pdf`.
- LaTeX source files: `main.tex`, `frontmatter/`, `chapters/`, `appendices/`, and `refs.bib`.
- Only the figure and table artifacts referenced by the thesis source.
- Public QR code files for direct thesis access.

## Excluded

This public package intentionally excludes raw COMSOL exports, `.mph` files, private lab/student-folder data, large intermediate data products, local machine paths, and model binary artifacts.

## Rebuilding

From a LaTeX environment with the required packages installed, run a normal BibTeX build sequence from the repository root:

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

The checked-in PDF is the canonical public copy for QR access.
