# Figure v3 visual quality assurance

The final 600 dpi PNG was opened at native resolution. The SVG was independently rendered in a browser at its exact intrinsic canvas size (510.236 × 538.583 pt) and compared with the PNG. No source workbook was read or modified during the v3 revision; all plotted values came from the existing analysis CSV files.

## Checks completed

- Layout: the compact 180 × 180 mm canvas uses a top overview row, a full-width chemical-family row and a bottom composition/transfer row. The PNG is 4,251 × 4,251 pixels at 600 dpi. Removing the UMAP panel leaves no empty grid cell.
- Panel a: Binary and Ternary headers remain centered over separate columns, with aligned values and fine separators.
- Panel b: `Pressure (kPa)` remains inside the panel, pressure is logarithmic and the narrow broken-axis tail retains all 25 high-temperature observations without repeated y labels.
- Panel c: the shared heading sits close to the two plots. c1 retains all 79 binary family pairs in the upper-triangular bubble matrix. c2 shows the 18 ternary triplets with the most experimental points, while explicitly reporting 49 triplets in total. Both subpanels use one absolute bubble-area scale of 12 pt² per unique system and a single shared size key; the c2-local size legend was removed.
- Panel d: the heading, subtitle and Binary/Ternary subheadings are separated after lowering both composition plots. The binary x1–y1 density and ternary simplex are fully visible with no clipping.
- Panel e: all four count/percentage annotations remain within the canvas and readable at manuscript width.
- Removed content: Morgan-fingerprint/UMAP points, their legend and the unresolved-structure annotation are absent from the manuscript figure. The underlying `molecular_space.csv` and molecular-analysis code are retained for later use.
- Vector parity: the independently rendered SVG matches the PNG in alignment, typography and content. No 3D, shadows, background gradients or decorative panel borders are present.
- Typography: the global font hierarchy and all panel-specific annotations were enlarged. All explanatory text, subtitles, tick labels and legend labels are black; gray remains only for non-text graphical elements such as grids, reference lines and size-key circles.

No unresolved overlap, clipping or excessive blank region was observed in the final PNG or SVG rendering.
