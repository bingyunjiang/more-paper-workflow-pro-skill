# Digitization Workflow

Use this when the only numerical evidence is a chart image or a PDF figure.

## Native entry

Every image/PDF starts with an immutable source preflight:

```bash
python scripts/figure_evidence_pipeline.py inspect \
  --input source.png \
  --chart-type line \
  --output-project figure-project.json

python scripts/figure_evidence_pipeline.py validate-project \
  --project figure-project.json
```

Omit `--chart-type` when unknown. The router then returns
`needs_chart_type_confirmation` and keeps value delivery unauthorized.

`figure-project.json` uses `morepaper.figure_project.v1` and records the source
SHA-256, original canvas or PDF page count, coordinate space, proposed route,
evidence contract, and three independent states:

- `extraction_status`: whether values have visible source support;
- `render_status`: whether a figure was rendered and checked;
- `delivery_status`: whether the complete evidence/delivery package passed.

## Candidate color-line baseline

The first native extractor is deliberately narrow: a color-distinct line in a
verified raster plot rectangle with explicit axis anchors.

```bash
python scripts/figure_evidence_pipeline.py extract-line \
  --project figure-project.json \
  --plot-bounds 40,20,620,420 \
  --x-anchor 40,0 --x-anchor 620,100 \
  --y-anchor 420,0 --y-anchor 20,1 \
  --series response=#cc2244 \
  --output-dir digitized
```

Use `--x-scale log10` or `--y-scale log10` only when visible ticks verify a
logarithmic axis. Add more anchors when available; a normalized calibration
residual above 0.02 blocks authorization.

The first run writes:

- `digitized_lines.csv`;
- `extraction_report.json`;
- `digitization_overlay.png`;
- `figure_project.result.json`.

Inspect `digitization_overlay.png` at the original raster resolution. If and
only if every accepted point follows the visible series and no legend,
annotation, axis, or missed curve is incorrectly represented, rerun the same
command with `--overlay-review accepted`. That accepted run may additionally
write `visualspec.json`.

Without accepted review, the result stays `extraction_status=needs_review`,
`value_delivery_authorized=false`, and no VisualSpec is materialized.
`value_delivery_authorized=true` means only that the candidate passed its
source-identity, calibration, coverage, and explicit overlay-review gates. It
is not evidence of author raw observations, hidden parameters, causal
mechanisms, or publication readiness.

## Binding evidence rules

1. Measure the exact source file recorded by SHA-256 and dimensions.
2. Never measure a preview, thumbnail, resized copy, overlay, or recreation.
3. Confirm the chart grammar, plot rectangle, axes, units, and scale before extraction.
4. Require at least two verified anchors per calibrated axis.
5. Segment only inside the verified plot rectangle; exclude legends, labels, arrows, and annotations.
6. Keep points, curves, bars, boxes, error bars, labels, and image regions as separate visible grammars.
7. Never interpolate a blank, occluded, fused, or unsupported span merely to complete a table.
8. Export original pixel/PDF coordinates beside mapped values and uncertainty.
9. Keep a coverage ledger or equivalent complete-cell/residual audit.
10. Treat official source data as a separate validation layer; never overwrite image-derived output.
11. Mark recovered values as `digitized_raster`, not raw experimental data.
12. Only an authorized extraction may materialize into the rendering/VisualSpec path.

Document any visual calibration, such as using a labeled peak or plateau when a crop edge is unreliable.

## Capability boundary

| Grammar | Native status |
|---|---|
| Color-distinct raster line | `candidate` |
| Scatter, simple/grouped/stacked bars | `planned` |
| Histogram and boxplot | `planned` |
| Heatmap, labelled pie/donut, aligned lattice | `planned` |
| Direct PDF vector recovery | preflight only; project-level assisted implementation required |

Do not route an unsupported grammar to the line extractor. A recognized but
unimplemented route must remain `not_extracted` or use an independently tested
project-level extractor with the same source and evidence contract.
