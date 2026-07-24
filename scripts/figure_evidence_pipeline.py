from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image, ImageDraw


SCHEMA_PROJECT = "morepaper.figure_project.v1"
SCHEMA_EXTRACTION = "morepaper.figure_extraction_evidence.v1"
SCHEMA_VALIDATION = "morepaper.figure_project_validation.v1"
RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
CHART_ROUTES: dict[str, dict[str, str]] = {
    "line": {"support": "candidate", "extractor": "native_color_line_v1"},
    "scatter": {"support": "planned", "extractor": "not_implemented"},
    "simple_bar": {"support": "planned", "extractor": "not_implemented"},
    "grouped_bar": {"support": "planned", "extractor": "not_implemented"},
    "stacked_bar": {"support": "planned", "extractor": "not_implemented"},
    "histogram": {"support": "planned", "extractor": "not_implemented"},
    "boxplot": {"support": "planned", "extractor": "not_implemented"},
    "heatmap": {"support": "planned", "extractor": "not_implemented"},
    "labelled_pie": {"support": "planned", "extractor": "not_implemented"},
    "aligned_lattice": {"support": "planned", "extractor": "not_implemented"},
}


class FigureEvidenceError(RuntimeError):
    """Fail-closed error for figure evidence operations."""


@dataclass(frozen=True)
class AxisCalibration:
    scale: str
    slope: float
    intercept: float
    anchors: tuple[tuple[float, float], ...]
    residuals: tuple[float, ...]
    normalized_max_residual: float

    def map_pixel(self, pixel: float) -> float:
        transformed = self.slope * pixel + self.intercept
        if self.scale == "log10":
            return 10.0**transformed
        return transformed

    def as_dict(self) -> dict[str, Any]:
        return {
            "scale": self.scale,
            "model": "transformed_value = slope * pixel + intercept",
            "slope": self.slope,
            "intercept": self.intercept,
            "anchors": [
                {
                    "pixel": pixel,
                    "value": value,
                    "residual_transformed_value": residual,
                }
                for (pixel, value), residual in zip(self.anchors, self.residuals)
            ],
            "normalized_max_residual": self.normalized_max_residual,
            "status": "pass" if self.normalized_max_residual <= 0.02 else "failed",
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def portable_relpath(path: Path, root: Path) -> str:
    return Path(os.path.relpath(path.resolve(), root.resolve())).as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FigureEvidenceError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise FigureEvidenceError(f"JSON root must be an object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def inspect_source(input_path: Path, chart_type: str | None, output_project: Path) -> dict[str, Any]:
    source = input_path.resolve()
    if not source.is_file():
        raise FigureEvidenceError(f"input does not exist: {input_path}")

    suffix = source.suffix.lower()
    input_record: dict[str, Any] = {
        "path": portable_relpath(source, output_project.parent),
        "display_name": source.name,
        "sha256": sha256_file(source),
        "size_bytes": source.stat().st_size,
    }
    if suffix in RASTER_SUFFIXES:
        with Image.open(source) as image:
            width, height = image.size
            mode = image.mode
        input_record.update(
            {
                "media_type": "raster_image",
                "width_px": width,
                "height_px": height,
                "pixel_mode": mode,
                "coordinate_space": "original_raster_pixels",
            }
        )
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise FigureEvidenceError("PDF inspection requires pypdf") from exc
        reader = PdfReader(str(source))
        input_record.update(
            {
                "media_type": "pdf",
                "page_count": len(reader.pages),
                "coordinate_space": "pdf_points",
            }
        )
    else:
        raise FigureEvidenceError(
            f"unsupported input suffix {suffix!r}; supported raster images and PDF"
        )

    normalized_chart_type = (chart_type or "").strip().lower()
    if not normalized_chart_type:
        route_status = "needs_chart_type_confirmation"
        route = {"support": "unknown", "extractor": "not_selected"}
        extraction_status = "needs_configuration"
    elif normalized_chart_type not in CHART_ROUTES:
        route_status = "unsupported_chart_type"
        route = {"support": "unsupported", "extractor": "not_available"}
        extraction_status = "not_extracted"
    else:
        route = CHART_ROUTES[normalized_chart_type]
        if route["support"] == "candidate" and input_record["media_type"] == "raster_image":
            route_status = "ready_for_configuration"
            extraction_status = "needs_configuration"
        elif input_record["media_type"] == "pdf":
            route_status = "pdf_requires_panel_and_representation_review"
            extraction_status = "needs_configuration"
        else:
            route_status = "recognized_not_implemented"
            extraction_status = "not_extracted"

    payload = {
        "schema": SCHEMA_PROJECT,
        "project_root": ".",
        "input": input_record,
        "chart": {
            "chart_type": normalized_chart_type or "unknown",
            "chart_type_verified": bool(normalized_chart_type in CHART_ROUTES),
        },
        "routing": {
            "status": route_status,
            "support_level": route["support"],
            "extractor": route["extractor"],
            "value_delivery_authorized": False,
        },
        "evidence_contract": {
            "source_identity_required": True,
            "measure_original_coordinates_only": True,
            "minimum_axis_anchors_per_axis": 2,
            "missing_values_are_not_interpolated": True,
            "overlay_review_required": True,
            "official_source_data_validation_is_separate": True,
        },
        "extraction_status": extraction_status,
        "render_status": "not_run",
        "delivery_status": "working",
    }
    _write_json(output_project, payload)
    return payload


def resolve_project_source(project_path: Path, project: dict[str, Any]) -> Path:
    input_record = project.get("input")
    if not isinstance(input_record, dict) or not isinstance(input_record.get("path"), str):
        raise FigureEvidenceError("project input.path is required")
    return (project_path.parent / input_record["path"]).resolve()


def validate_project(project_path: Path, *, verify_source: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    try:
        project = _load_json(project_path)
    except FigureEvidenceError as exc:
        return {
            "schema": SCHEMA_VALIDATION,
            "status": "failed",
            "errors": [str(exc)],
        }

    if project.get("schema") != SCHEMA_PROJECT:
        errors.append(f"schema must be {SCHEMA_PROJECT}")
    for field in (
        "input",
        "chart",
        "routing",
        "evidence_contract",
        "extraction_status",
        "render_status",
        "delivery_status",
    ):
        if field not in project:
            errors.append(f"missing required field: {field}")

    input_record = project.get("input")
    if isinstance(input_record, dict):
        for field in ("path", "sha256", "media_type", "coordinate_space"):
            if not input_record.get(field):
                errors.append(f"missing input.{field}")
        if input_record.get("media_type") == "raster_image":
            for field in ("width_px", "height_px"):
                if not isinstance(input_record.get(field), int) or input_record[field] <= 0:
                    errors.append(f"input.{field} must be a positive integer")
    else:
        errors.append("input must be an object")

    if verify_source and isinstance(input_record, dict) and input_record.get("path"):
        try:
            source = resolve_project_source(project_path, project)
            if not source.is_file():
                errors.append(f"source file missing: {input_record['path']}")
            else:
                actual_hash = sha256_file(source)
                if actual_hash != input_record.get("sha256"):
                    errors.append("source SHA-256 mismatch")
                if input_record.get("media_type") == "raster_image":
                    with Image.open(source) as image:
                        actual_size = image.size
                    expected_size = (
                        input_record.get("width_px"),
                        input_record.get("height_px"),
                    )
                    if actual_size != expected_size:
                        errors.append(
                            f"source dimensions mismatch: expected {expected_size}, got {actual_size}"
                        )
        except (OSError, FigureEvidenceError) as exc:
            errors.append(str(exc))

    return {
        "schema": SCHEMA_VALIDATION,
        "project": project_path.name,
        "status": "pass" if not errors else "failed",
        "source_identity_verified": verify_source and not any(
            "source" in error.lower() for error in errors
        ),
        "errors": errors,
    }


def parse_bounds(value: str) -> tuple[int, int, int, int]:
    try:
        parts = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise FigureEvidenceError("plot bounds must be left,top,right,bottom integers") from exc
    if len(parts) != 4:
        raise FigureEvidenceError("plot bounds must contain four integers")
    left, top, right, bottom = parts
    if left < 0 or top < 0 or right <= left or bottom <= top:
        raise FigureEvidenceError("plot bounds must satisfy 0 <= left < right and 0 <= top < bottom")
    return left, top, right, bottom


def parse_anchor(value: str) -> tuple[float, float]:
    try:
        pixel_text, value_text = value.split(",", 1)
        return float(pixel_text.strip()), float(value_text.strip())
    except ValueError as exc:
        raise FigureEvidenceError("axis anchor must be pixel,value") from exc


def parse_series(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise FigureEvidenceError("series must be name=#RRGGBB")
    name, color = (part.strip() for part in value.split("=", 1))
    if not name:
        raise FigureEvidenceError("series name cannot be empty")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        raise FigureEvidenceError("series color must be #RRGGBB")
    return name, color.lower()


def hex_rgb(value: str) -> tuple[int, int, int]:
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def fit_axis(anchors: Iterable[tuple[float, float]], scale: str) -> AxisCalibration:
    anchor_list = tuple(anchors)
    if len(anchor_list) < 2:
        raise FigureEvidenceError("at least two anchors are required per axis")
    pixels = np.asarray([item[0] for item in anchor_list], dtype=float)
    values = np.asarray([item[1] for item in anchor_list], dtype=float)
    if len(set(float(item) for item in pixels)) < 2:
        raise FigureEvidenceError("axis anchors require at least two distinct pixel positions")
    if scale == "log10":
        if np.any(values <= 0):
            raise FigureEvidenceError("log10 axis anchors require positive values")
        transformed = np.log10(values)
    elif scale == "linear":
        transformed = values
    else:
        raise FigureEvidenceError("axis scale must be linear or log10")

    matrix = np.column_stack([pixels, np.ones_like(pixels)])
    slope, intercept = np.linalg.lstsq(matrix, transformed, rcond=None)[0]
    predicted = slope * pixels + intercept
    residuals = transformed - predicted
    span = float(np.ptp(transformed))
    denominator = span if span > 0 else 1.0
    normalized = float(np.max(np.abs(residuals)) / denominator)
    if not math.isfinite(float(slope)) or abs(float(slope)) < 1e-15:
        raise FigureEvidenceError("axis calibration slope is invalid")
    return AxisCalibration(
        scale=scale,
        slope=float(slope),
        intercept=float(intercept),
        anchors=anchor_list,
        residuals=tuple(float(item) for item in residuals),
        normalized_max_residual=normalized,
    )


def _validate_bounds(
    bounds: tuple[int, int, int, int], width: int, height: int
) -> None:
    left, top, right, bottom = bounds
    if right >= width or bottom >= height:
        raise FigureEvidenceError(
            f"plot bounds {bounds} exceed source canvas {width}x{height}"
        )


def _line_points_for_color(
    rgb: np.ndarray,
    bounds: tuple[int, int, int, int],
    target_rgb: tuple[int, int, int],
    tolerance: float,
    max_vertical_span_px: int,
) -> tuple[list[tuple[int, float]], dict[str, int]]:
    left, top, right, bottom = bounds
    crop = rgb[top : bottom + 1, left : right + 1].astype(np.int32)
    target = np.asarray(target_rgb, dtype=np.int32)
    distances = np.sqrt(np.sum((crop - target) ** 2, axis=2))
    mask = distances <= tolerance

    accepted: list[tuple[int, float]] = []
    counts = {"accepted": 0, "missing": 0, "ambiguous_vertical_span": 0}
    for column_index, x_pixel in enumerate(range(left, right + 1)):
        local_y = np.flatnonzero(mask[:, column_index])
        if local_y.size == 0:
            counts["missing"] += 1
            continue
        span = int(local_y[-1] - local_y[0])
        if span > max_vertical_span_px:
            counts["ambiguous_vertical_span"] += 1
            continue
        y_pixel = float(np.median(local_y) + top)
        accepted.append((x_pixel, y_pixel))
        counts["accepted"] += 1
    return accepted, counts


def _pixel_uncertainty(axis: AxisCalibration, pixel: float) -> float:
    center = axis.map_pixel(pixel)
    return max(
        abs(axis.map_pixel(pixel - 0.5) - center),
        abs(axis.map_pixel(pixel + 0.5) - center),
    )


def _visualspec_from_series(
    width: int,
    height: int,
    x_axis: AxisCalibration,
    y_axis: AxisCalibration,
    series_rows: dict[str, list[dict[str, Any]]],
    colors: dict[str, str],
) -> dict[str, Any]:
    plots: list[dict[str, Any]] = []
    for name, rows in series_rows.items():
        plots.append(
            {
                "type": "line",
                "label": name,
                "data": {
                    "x": [row["x"] for row in rows],
                    "y": [row["y"] for row in rows],
                },
                "style": {"color": colors[name], "line_width_pt": 1.2},
            }
        )

    x_values = [anchor[1] for anchor in x_axis.anchors]
    y_values = [anchor[1] for anchor in y_axis.anchors]
    return {
        "schema": "scientificfigure.visualspec.v2",
        "figure": {
            "size_mm": [100.0, round(100.0 * height / width, 3)],
            "dpi": 300,
            "crop_mode": "fixed_canvas",
            "background": "white",
        },
        "theme": {
            "font": {
                "family_candidates": ["Arial", "Liberation Sans", "DejaVu Sans"],
                "size_pt": 8,
            }
        },
        "panels": [
            {
                "id": "digitized_panel",
                "bbox_normalized": [0.16, 0.16, 0.78, 0.74],
                "source_strategy": "digitized_raster",
                "representation": "semantic_vector",
                "axes": {
                    "x": {
                        "scale": "log" if x_axis.scale == "log10" else "linear",
                        "limits": [min(x_values), max(x_values)],
                    },
                    "y": {
                        "scale": "log" if y_axis.scale == "log10" else "linear",
                        "limits": [min(y_values), max(y_values)],
                    },
                },
                "plots": plots,
                "annotations": [],
            }
        ],
    }


def extract_color_lines(
    project_path: Path,
    output_dir: Path,
    *,
    plot_bounds: tuple[int, int, int, int],
    x_anchors: Iterable[tuple[float, float]],
    y_anchors: Iterable[tuple[float, float]],
    series: Iterable[tuple[str, str]],
    x_scale: str = "linear",
    y_scale: str = "linear",
    color_tolerance: float = 36.0,
    minimum_coverage: float = 0.65,
    max_vertical_span_px: int = 12,
    overlay_review_status: str = "pending",
) -> dict[str, Any]:
    project = _load_json(project_path)
    validation = validate_project(project_path, verify_source=True)
    if validation["status"] != "pass":
        raise FigureEvidenceError("; ".join(validation["errors"]))
    if project.get("chart", {}).get("chart_type") != "line":
        raise FigureEvidenceError("native_color_line_v1 requires chart.chart_type=line")
    if project.get("input", {}).get("media_type") != "raster_image":
        raise FigureEvidenceError("native_color_line_v1 requires a raster image")

    source = resolve_project_source(project_path, project)
    with Image.open(source) as original:
        image = original.convert("RGB")
    width, height = image.size
    _validate_bounds(plot_bounds, width, height)

    series_list = list(series)
    if not series_list:
        raise FigureEvidenceError("at least one --series name=#RRGGBB is required")
    if len({name for name, _ in series_list}) != len(series_list):
        raise FigureEvidenceError("series names must be unique")

    x_axis = fit_axis(x_anchors, x_scale)
    y_axis = fit_axis(y_anchors, y_scale)
    rgb = np.asarray(image)
    series_rows: dict[str, list[dict[str, Any]]] = {}
    coverage_ledger: list[dict[str, Any]] = []
    colors = dict(series_list)
    total_columns = plot_bounds[2] - plot_bounds[0] + 1

    for name, color in series_list:
        points, counts = _line_points_for_color(
            rgb,
            plot_bounds,
            hex_rgb(color),
            color_tolerance,
            max_vertical_span_px,
        )
        rows: list[dict[str, Any]] = []
        for x_pixel, y_pixel in points:
            rows.append(
                {
                    "series": name,
                    "x": x_axis.map_pixel(x_pixel),
                    "y": y_axis.map_pixel(y_pixel),
                    "x_px": x_pixel,
                    "y_px": y_pixel,
                    "uncertainty_x": _pixel_uncertainty(x_axis, x_pixel),
                    "uncertainty_y": _pixel_uncertainty(y_axis, y_pixel),
                    "status": "visible_color_supported",
                }
            )
        series_rows[name] = rows
        coverage = len(rows) / total_columns
        coverage_ledger.append(
            {
                "series": name,
                "declared_columns": total_columns,
                "accepted_columns": len(rows),
                "missing_columns": counts["missing"],
                "ambiguous_columns": counts["ambiguous_vertical_span"],
                "coverage": coverage,
                "status": "pass" if coverage >= minimum_coverage else "failed",
            }
        )

    calibration_pass = (
        x_axis.normalized_max_residual <= 0.02
        and y_axis.normalized_max_residual <= 0.02
    )
    coverage_pass = all(item["status"] == "pass" for item in coverage_ledger)
    any_rows = any(series_rows.values())
    candidate_gates_pass = calibration_pass and coverage_pass and any_rows
    overlay_review_accepted = overlay_review_status == "accepted"
    authorized = candidate_gates_pass and overlay_review_accepted
    if authorized:
        extraction_status = "authorized_candidate"
    elif candidate_gates_pass:
        extraction_status = "needs_review"
    elif any_rows:
        extraction_status = "partial_visible"
    else:
        extraction_status = "not_extracted"

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "digitized_lines.csv"
    fieldnames = [
        "series",
        "x",
        "y",
        "x_px",
        "y_px",
        "uncertainty_x",
        "uncertainty_y",
        "status",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for name, _ in series_list:
            writer.writerows(series_rows[name])

    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    left, top, right, bottom = plot_bounds
    draw.rectangle((left, top, right, bottom), outline=(255, 0, 255), width=1)
    for name, color in series_list:
        overlay_color = hex_rgb(color)
        for row in series_rows[name]:
            x_pixel = int(row["x_px"])
            y_pixel = int(round(row["y_px"]))
            draw.ellipse(
                (x_pixel - 1, y_pixel - 1, x_pixel + 1, y_pixel + 1),
                outline=overlay_color,
            )
    overlay_path = output_dir / "digitization_overlay.png"
    overlay.save(overlay_path)

    visualspec_path: Path | None = None
    if authorized:
        visualspec = _visualspec_from_series(
            width, height, x_axis, y_axis, series_rows, colors
        )
        visualspec_path = output_dir / "visualspec.json"
        _write_json(visualspec_path, visualspec)

    report = {
        "schema": SCHEMA_EXTRACTION,
        "extractor": {
            "id": "native_color_line_v1",
            "support_level": "candidate",
            "claim": "visible color-supported curve coordinates only",
        },
        "input_contract": {
            "path": project["input"]["path"],
            "sha256": project["input"]["sha256"],
            "width_px": width,
            "height_px": height,
            "coordinate_space": "original_raster_pixels",
            "source_identity_verified": True,
        },
        "plot_bounds_px": list(plot_bounds),
        "calibration": {"x": x_axis.as_dict(), "y": y_axis.as_dict()},
        "configuration": {
            "color_tolerance": color_tolerance,
            "minimum_coverage": minimum_coverage,
            "max_vertical_span_px": max_vertical_span_px,
            "missing_values_interpolated": False,
            "overlay_review_status": overlay_review_status,
        },
        "coverage_ledger": coverage_ledger,
        "residual_audit": {
            "status": "pass" if calibration_pass else "failed",
            "x_normalized_max_residual": x_axis.normalized_max_residual,
            "y_normalized_max_residual": y_axis.normalized_max_residual,
        },
        "artifacts": {
            "csv": csv_path.name,
            "overlay": overlay_path.name,
            "visualspec": visualspec_path.name if visualspec_path else None,
        },
        "value_delivery_authorized": authorized,
        "extraction_status": extraction_status,
        "render_status": "not_run",
        "delivery_status": "working",
        "limitations": [
            "candidate extractor; original-resolution overlay review remains required",
            "does not recover hidden observations, author fit parameters, or occluded spans",
            "same-color legends, annotations, crossings, and thick vertical strokes "
            "require a tighter verified plot ROI",
        ],
    }
    report_path = output_dir / "extraction_report.json"
    _write_json(report_path, report)

    result_project = dict(project)
    result_project["extraction_status"] = extraction_status
    result_project["render_status"] = "not_run"
    result_project["delivery_status"] = "working"
    result_project["routing"] = dict(project["routing"])
    result_project["routing"]["value_delivery_authorized"] = authorized
    result_project["artifacts"] = {
        "extraction_report": report_path.name,
        "digitized_csv": csv_path.name,
        "overlay": overlay_path.name,
        "visualspec": visualspec_path.name if visualspec_path else None,
    }
    _write_json(output_dir / "figure_project.result.json", result_project)
    return report


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Native source-locked figure evidence pipeline for more-paper-workflow."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect", help="Fingerprint an image/PDF and create a fail-closed figure project."
    )
    inspect_parser.add_argument("--input", required=True, type=Path)
    inspect_parser.add_argument("--chart-type", choices=sorted(CHART_ROUTES))
    inspect_parser.add_argument("--output-project", required=True, type=Path)

    validate_parser = subparsers.add_parser(
        "validate-project", help="Validate a figure project and recheck source identity."
    )
    validate_parser.add_argument("--project", required=True, type=Path)
    validate_parser.add_argument("--json-out", type=Path)

    extract_parser = subparsers.add_parser(
        "extract-line",
        help="Candidate extraction of color-distinct raster lines with explicit calibration.",
    )
    extract_parser.add_argument("--project", required=True, type=Path)
    extract_parser.add_argument("--plot-bounds", required=True)
    extract_parser.add_argument("--x-anchor", action="append", required=True)
    extract_parser.add_argument("--y-anchor", action="append", required=True)
    extract_parser.add_argument("--series", action="append", required=True)
    extract_parser.add_argument("--x-scale", choices=["linear", "log10"], default="linear")
    extract_parser.add_argument("--y-scale", choices=["linear", "log10"], default="linear")
    extract_parser.add_argument("--color-tolerance", type=float, default=36.0)
    extract_parser.add_argument("--minimum-coverage", type=float, default=0.65)
    extract_parser.add_argument("--max-vertical-span-px", type=int, default=12)
    extract_parser.add_argument(
        "--overlay-review",
        choices=["pending", "accepted"],
        default="pending",
        help="Set accepted only after inspecting the generated overlay at original resolution.",
    )
    extract_parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            payload = inspect_source(args.input, args.chart_type, args.output_project)
            _print(payload)
            return 0
        if args.command == "validate-project":
            payload = validate_project(args.project, verify_source=True)
            if args.json_out:
                _write_json(args.json_out, payload)
            _print(payload)
            return 0 if payload["status"] == "pass" else 2
        if args.command == "extract-line":
            if not 0 < args.minimum_coverage <= 1:
                raise FigureEvidenceError("minimum coverage must be in (0, 1]")
            if args.color_tolerance < 0:
                raise FigureEvidenceError("color tolerance must be non-negative")
            if args.max_vertical_span_px < 0:
                raise FigureEvidenceError("max vertical span must be non-negative")
            payload = extract_color_lines(
                args.project,
                args.output_dir,
                plot_bounds=parse_bounds(args.plot_bounds),
                x_anchors=[parse_anchor(value) for value in args.x_anchor],
                y_anchors=[parse_anchor(value) for value in args.y_anchor],
                series=[parse_series(value) for value in args.series],
                x_scale=args.x_scale,
                y_scale=args.y_scale,
                color_tolerance=args.color_tolerance,
                minimum_coverage=args.minimum_coverage,
                max_vertical_span_px=args.max_vertical_span_px,
                overlay_review_status=args.overlay_review,
            )
            _print(payload)
            return 0 if payload["value_delivery_authorized"] else 3
        parser.error(f"unknown command: {args.command}")
    except FigureEvidenceError as exc:
        _print(
            {
                "schema": "morepaper.figure_pipeline_error.v1",
                "status": "failed",
                "error": str(exc),
            }
        )
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
