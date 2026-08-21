# Figure visual quality assurance

The final 600 dpi PNG was opened and inspected at its native resolution after export. The PDF and SVG were regenerated from the same Matplotlib figure object.

## Checks completed

- Canvas: white background, approximately 180 mm wide, with six consistently spaced panels.
- Labels: `(a)`–`(f)` are bold, aligned and not clipped; axis titles and tick labels remain readable at final size.
- Legends: no legend obscures a data cloud. The molecular-space panel reserves an empty upper band for its legend and an empty lower band for structure-resolution notes.
- State space: pressure is explicitly logarithmic; contours convey the dense region while low-alpha points preserve rare high-temperature/high-pressure coverage.
- Composition: the binary liquid–vapor density and ternary barycentric simplex are legible, with no overlapping vertex labels.
- Molecular space: small semitransparent markers, distinct shapes and a projected/total legend make the missing ternary-only structures explicit without fabricating coordinates.
- Density and subsystem panels: rank-frequency axes are logarithmic; stacked-bar counts and percentages do not collide.
- Styling: binary/ternary colors are consistent, shared molecules use a muted purple, and line/marker shapes remain distinguishable in grayscale.
- Export: PNG is 4,148 × 3,098 pixels at 600 dpi; PDF and SVG retain vector text and graphical elements.

## Adjustment made after preview

The first preview placed the molecular-space legend and missing-structure note over a few UMAP points. Extra vertical plotting range was added so both annotations now occupy data-free regions. The final files were then regenerated and visually rechecked.
