# JRTPM (Elsevier) manuscript

Submission package for the **Journal of Rail Transport Planning &
Management** (Elsevier). Converted from the IEEE conference version in
`../main.tex`.

## Build

```bash
pdflatex main
bibtex   main
pdflatex main
pdflatex main
```

Requires `cas-dc.cls`, `cas-common.sty`, and `cas-model2-names.bst` (copied
here from `els-cas-templates/`, which is kept pristine and is not modified).

## Files to submit

### remember to not open-source while uploading as it might charge the auhor money

Upload exactly these. Nothing else in this folder goes to the journal.

**Required**

| File | Notes |
|---|---|
| `main.tex` | Manuscript source — **the only required source file** |
| `refs.bib` | Bibliography (author-year style) |
| `highlights.txt` | 4 bullets, each ≤ 85 characters |
| `system_architecture.png` | Fig. 1 — 3868 px, 1172 dpi at single column |
| `journey_state_diagram.png` | Fig. 2 — 3543 px, 1074 dpi at single column |
| `train_18238_station_delay_30d.pdf` | Fig. 3 — **vector** |
| `alpha_profile_plot.pdf` | Fig. 4 — **vector** |

**Also required** — Elsevier asks for all editable sources, and `main.tex`
will not compile without them:

| File | Notes |
|---|---|
| `cas-dc.cls` | Elsevier CAS class |
| `cas-common.sty` | CAS shared style |
| `cas-model2-names.bst` | Bibliography style |
| `thumbnails/` | 6 × `.jpeg` — CAS references `cas-email.jpeg` for the correspondence icon |

**Do not submit:** `main.pdf`, `main.aux`, `main.bbl`, `main.blg`,
`main.log`, `main.out`, `main.abs`, `.cache/`, `README.md`, `regen_figures.py`,
the `.png` copies of Figs 3–4, `diagram_*.mmd`, and the
`els-cas-templates/` and `misc/` folders.

Build intermediates are git-ignored. `main.pdf` is currently **untracked but
not ignored** — it is a build product, not a submission file.

## Figures

The two data figures are **vector PDFs** — 0 embedded rasters, 2650 and 195
vector paths respectively — which is Elsevier's preferred format for line art
and sidesteps the 1000 dpi raster requirement entirely. Both are reproduced
exactly from the corresponding cells in `notebooks/first.ipynb` by:

```bash
python docs/sati_conference/elsevier/regen_figures.py
```

Runs in about 4 seconds. Requires only **matplotlib, pandas and pymupdf** from
the project venv — no Kaleido, svglib or reportlab. The prepared frame is
cached in `.cache/rail_frame_18238.pkl`, invalidated by mtime against the CSV
and the static route JSONs, so repeat runs skip the reload.

Why matplotlib rather than Plotly (the notebook still uses Plotly
interactively):

- Kaleido's direct PDF export **silently rasterises** into a single full-page
  bitmap — a valid-looking PDF with no vector content. Detectable only by
  inspecting `page.get_images()`.
- Kaleido's SVG export *is* vector, but converting it via svglib took ~108 s
  and produced a **black page**: Plotly emits bare clip-path rects with no
  `fill`, and svglib resolves unset fill to PDF's black default.
- matplotlib writes true vector PDF directly and is orders of magnitude faster.

`regen_figures.py` validates both PDFs before returning and raises on a
missing/truncated file, a full-page bitmap, a raster-only figure, or a black
or non-white page — so a bad artefact cannot ship silently.

PNG copies are written for convenience but are **not** what the manuscript
includes.

### Figures 1 and 2 (architecture, state machine)

These two are **raster**, authored as Mermaid diagrams in
`../../implementation_plan.md`. Re-export them from that source if a
higher-quality version is ever available; the current PNGs satisfy Elsevier's
1000 dpi single-column minimum.

`diagram_architecture.mmd` and `diagram_state_machine.mmd` in this folder are
verbatim copies of the two relevant Mermaid blocks, kept as a convenience.
They are referenced by nothing and are not submission files.

Note: a true vector re-render requires `mermaid-cli`, which pulls in a
headless Chromium (~1.1 GB installed). Not worth it for two schematics that
already clear the resolution bar.

## CAS class pitfalls (hard-won; keep in mind before editing)

These are not obvious from the template and cost real time to rediscover.

1. **Never enable microtype character expansion.** `cas-common.sty` ships STIX
   fonts that pdfTeX cannot expand, so `\microtypesetup{expansion=...}` aborts
   the run. `\hbadness=1000 \vbadness=1000 \raggedbottom \sloppy` is enough.
2. **Never trust pdflatex's exit code.** A deleted figure logs
   `File ... not found: using draft setting` and still exits 0, leaving an
   empty frame. Grep `main.log` for `not found`.
3. **A fatal error truncates `main.aux`,** so BibTeX then reports
   "I found no \bibdata command" and every citation becomes undefined *while
   the build still exits 0*. Clean-rebuild by deleting `.aux`/`.bbl`/`.blg`.
4. **CAS records the page total from `\AtEndDocument`,** which fires *before*
   deferred `table*` floats are flushed, so the footer reads "Page N of M" with
   M too small. A `\clearpage` immediately before `\end{document}` makes the
   recorded total match reality.
5. **CAS draws a footer rule at y = 754.0 pt** on a4paper (`\textheight` =
   689.41 pt, page height 793.7 pt). Checking a float against the *page edge*
   rather than this rule will wrongly report "fits" while the table actually
   collides with the footer text.
6. **`longtable` / `\ContinuedFloat` cannot be used** with a two-column
   `table*` in `cas-dc`. To continue one table over a page break, emit a second
   `table*` inside a `\begingroup` and use `\addtocounter{table}{-1}` plus
   `\renewcommand{\thetable}{8 (continued)}` so it is not numbered separately.
7. **The class files must sit next to `main.tex`** — pdflatex cannot resolve
   them from `els-cas-templates/`. `thumbnails/` is also required (CAS
   references `thumbnails/cas-email.jpeg` for the correspondence icon).

## Compliance status

Checked against `misc/guide_for_authors.md`:

| Requirement | Status |
|---|---|
| CAS LaTeX template | ✅ `cas-dc` |
| Abstract ≤ 250 words | ✅ 224 |
| Keywords 1–7, English | ✅ 6 |
| Highlights 3–5 bullets ≤ 85 chars, separate file | ✅ 4 bullets, 64–74 chars |
| References cited ↔ listed | ✅ 15 = 15 |
| Tables editable, consecutively numbered, all cited | ✅ 9 tables |
| No vertical rules or shading | ✅ |
| Figures cited, separate files | ✅ 4 |
| Artwork ≥ 1000 dpi | ✅ 1172 / 1074 dpi |
| Vector line art where possible | ✅ Figs 3–4 vector |
| Funding statement (guide wording) | ✅ |
| Competing-interest declaration (manuscript text) | ✅ |
| Generative-AI declaration | ✅ |
| Data statement | ⚠️ see below |

### Required in the submission system — not in any file

Two checklist items live in Elsevier's online system and **cannot be
satisfied by the manuscript source**. Neither has been done yet:

1. **Competing-interests declaration upload.** The guide requires the
   Elsevier *declarations tool* to be completed for **all authors**, and the
   resulting Word document uploaded at the "attach/upload files" step, saved
   as `.doc`/`.docx`. Author signatures are not required. Authors with nothing
   to declare should select *"I have nothing to declare."*

   The `\section*{Declaration of competing interest}` in `main.tex` covers
   only the **manuscript text** — it is **not** a substitute for this upload.
   Doing this is the most likely reason a submission gets bounced at the
   attach-files step.

2. **Open-access APC responsibility.** If the article is submitted as open
   access, **all** authors must understand that they are responsible for paying
   the Article Publishing Charge if accepted. Payment may be covered by the
   corresponding author's institution or the research funder. This is
   acknowledged as part of the publishing agreement after acceptance, but
   confirm author availability before selecting OA.

   JRTPM supports OA, and eligibility for a publishing agreement is based on
   the **corresponding author's** affiliation only.

## Outstanding items before submission

1. **Data availability** points at a Google Form. JRTPM applies **Option B**
   of its research-data policy: authors are *encouraged* to deposit in a
   repository and cite the dataset, but if that is not possible, a statement
   explaining why is acceptable. The current wording satisfies the fallback,
   so this is optional — a Zenodo deposit with a DOI would strengthen it.
2. **`flier2009delay` has no page numbers.** The entry carries a DOI
   (`10.4230/DROPS/2009.2737`) and publisher details, but BibTeX still warns
   about the empty `pages` field on every build. Adding the page numbers from
   the DROPS record will silence it.
3. **Residual LaTeX warnings, both benign.** `Float too large for page by
   2.65pt` points at Table 9, whose measured extent is 13.9 pt *inside* the
   trim with all 20 rows rendering. `Overfull \hbox (123.63pt)` sits inside the
   CAS `main.abs` environment, renders correctly, and does not reproduce on the
   stock Elsevier sample.
4. **Figures 1 and 2 are raster.** Both clear 1000 dpi. Vector would be
   preferable but needs the ~1.1 GB mermaid-cli toolchain — see above.
