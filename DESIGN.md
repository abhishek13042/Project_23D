---
name: Project 23D
description: A survey sheet for a kidney tumor segmentation model. Every test scan is a real spot on a contour map.
colors:
  sheet: "#12384a"
  sheet-deep: "#0b2633"
  sheet-line: "#3f6e80"
  on-sheet: "#e9f2f2"
  on-sheet-soft: "#aec8cd"
  paper: "#eaf0f1"
  paper-deep: "#dae3e6"
  ink: "#0f2a36"
  ink-soft: "#46606c"
  rule: "#b4c4ca"
  link: "#0c5f78"
  mark: "#f2b544"
  warn: "#99300f"
  film: "#0e1012"
  film-raised: "#1a1d20"
  film-line: "#43474b"
  film-ink: "#e8eaeb"
  film-soft: "#a7abae"
  label-kidney: "#0fa596"
  label-tumor: "#e2562f"
  label-cyst: "#9a7cf0"
typography:
  display:
    fontFamily: Archivo
    fontWeight: 600
    fontStretch: 116%
  body:
    fontFamily: Archivo
    fontWeight: 400
    fontSize: 17px
    lineHeight: 1.6
  note:
    fontFamily: Source Serif 4
    fontStyle: italic
    fontWeight: 400
rounded:
  control: 2px
spacing:
  page: 1240px
  measure: 66ch
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: 11px 20px
  button-primary-hover:
    backgroundColor: "{colors.link}"
    textColor: "#ffffff"
  button-primary-disabled:
    backgroundColor: "{colors.paper-deep}"
    textColor: "{colors.ink-soft}"
  button-sheet:
    backgroundColor: "{colors.on-sheet}"
    textColor: "{colors.sheet-deep}"
    rounded: "{rounded.control}"
    padding: 11px 20px
  button-sheet-hover:
    backgroundColor: "{colors.mark}"
    textColor: "{colors.sheet-deep}"
---

# Design System: Project 23D

## 1. Overview

**Creative North Star: "The Survey"**

The site reads like a survey sheet of the model's results. The hero is a contour map of the 73 test scans, drawn from real scores, and its lowest scan is shown first. Failures are part of the map, not a footnote.

## 2. Colors

Deep teal sheets carry the map and the viewer's surroundings. Pale paper carries reading and tables. Near-black film is reserved for CT.

### Named Rules

**The Label Rule.** Teal, orange and violet mean kidney, tumor and cyst, and nothing else. They pass the palette validator's colorblind checks.

**The Survey Mark Rule.** Amber marks the current place or the lowest scans. It always comes with a shape, so color never carries the meaning alone.

## 3. Typography

Archivo, stretched to 116% width, sets headings and the big scores. Archivo at normal width sets body text and tables, with tabular numerals. Source Serif 4 italic is only for map notes and source notes. Body text stays within 66ch.

## 4. Layout

Full-width sheets alternate with paper. Page content sits in a 1240px frame. The phone layout swaps the wide map for a tall one, so labels stay readable.

## 5. Elevation & Depth

The system is flat. Depth comes from the contour bands and from the change between sheet and paper, not from shadows.

## 6. Shapes

Corners are 2px. Buttons are ink on paper, and light on the map sheet, where hover turns them amber. Boxes are thin ruled lines, like the title block of a printed map.

## 7. Components

- **Score terrain:** a contour map of mean Dice by tumor and kidney size. Each spot is a real scan, and a key explains every mark. The contours between spots are smoothed, and the page says so. The table of all 73 scans gives the same data as text.
- **Reading:** a side panel that names the scan being pointed at.
- **Ruler:** one 0 to 1 scale bar with a dot for the mean and a band for the 95% interval. Every score uses this same ruler.
- **Ledger:** a ruled table. Ruled tables with a scale share fixed columns, so they line up from one table to the next.
- **Viewer:** a film-black NiiVue panel with Model, Expert and CT-only views.
- **Drop zone:** the whole area is one target. It stays locked until the consent box is ticked, and the upload rules come before it.
- **Title block:** a footer of data, model, viewer and license credits.

## 8. Do's and Don'ts

### Do:

- **Do** show the worst scan first and name the failures.
- **Do** read every number from the generated results data.
- **Do** keep "Research demo, not for clinical use." on every page.
- **Do** keep the contour draw-in as the one authored motion, and turn it off for reduced motion.

### Don't:

- **Don't** type scores by hand or make clinical claims.
- **Don't** use label colors for decoration.
- **Don't** add shadows, gradient text, glass, or thick colored side borders.
- **Don't** add a second kind of score chart.
