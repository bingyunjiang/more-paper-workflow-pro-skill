#!/usr/bin/env python3
"""Scan a Zotero MinerU ZIP cache and prepare Step 7 figure assets."""

from __future__ import annotations

try:
    from console_compat import configure_console_output

    configure_console_output()
except Exception:
    pass

import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from workflow_contracts import FigureIndexRecord, inspect_mineru_zip, write_figure_index  # noqa: E402


def _read_zip_json(zf: zipfile.ZipFile, name: str) -> dict[str, Any]:
    try:
        return json.loads(zf.read(name).decode("utf-8"))
    except KeyError:
        return {}


def _slug(value: str, fallback: str) -> str:
    text = re.sub(r"[^\w.-]+", "-", value.strip(), flags=re.UNICODE).strip("-")
    return text[:80] or fallback


def _iter_manifest_figures(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    figures: list[dict[str, Any]] = []
    for section_index, section in enumerate(manifest.get("sections") or [], start=1):
        section_heading = str(section.get("heading") or "")
        section_id = f"section-{section_index:02d}"
        for fig in section.get("figures") or []:
            if not isinstance(fig, dict):
                continue
            figures.append({
                "section_id": section_id,
                "section_heading": section_heading,
                **fig,
            })
    for fig in manifest.get("allFigures") or []:
        if isinstance(fig, dict):
            figures.append({"section_id": "", "section_heading": "", **fig})
    return figures


def scan_mineru_zip(zip_path: Path, output: Path, figures_dir: Path | None, copy_images: bool) -> int:
    summary = inspect_mineru_zip(zip_path)
    if "bad_zip" in summary.warnings or "zip_missing" in summary.warnings:
        raise SystemExit(f"Cannot read MinerU ZIP: {zip_path}")

    records: list[FigureIndexRecord] = []
    copied: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        manifest = _read_zip_json(zf, "manifest.json")
        figures = _iter_manifest_figures(manifest)

        for index, fig in enumerate(figures, start=1):
            image_path = str(fig.get("path") or "")
            if not image_path:
                continue
            label = str(fig.get("label") or f"image-{index}")
            page = str(fig.get("page") if fig.get("page") is not None else "")
            caption = str(fig.get("caption") or "")
            local_image_path = ""
            if copy_images and figures_dir:
                suffix = Path(image_path).suffix or ".jpg"
                filename = f"{_slug(label, f'fig-{index:03d}')}{suffix}"
                target = figures_dir / filename
                figures_dir.mkdir(parents=True, exist_ok=True)
                try:
                    with zf.open(image_path) as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    local_image_path = target.as_posix()
                    copied.append(local_image_path)
                except KeyError:
                    local_image_path = ""

            source_type = "caption_plus_text" if caption else "visual_pending"
            records.append(FigureIndexRecord(
                item_key=summary.parent_item_key,
                figure_id=label,
                figure_type="figure",
                page=page,
                caption=caption,
                mentions_in_text=[],
                source_type=source_type,
                source_item_key=summary.parent_item_key,
                source_attachment_key=summary.attachment_key,
                source_image_path=image_path,
                local_image_path=local_image_path,
                section_id=str(fig.get("section_id") or ""),
                claim_binding="",
            ))

    metadata = {
        "source_zip": zip_path.as_posix(),
        "mineru_zip_summary": summary.__dict__,
        "copied_images": copied,
        "notes": [
            "MinerU images are candidates only until bound to a claim.",
            "PDF remains the truth source for captions, tables, equations, and strong claims.",
        ],
    }
    write_figure_index(output, records, metadata)
    print(f"FIGURE_INDEX: {output}")
    print(f"FIGURES: {len(records)}")
    if copied:
        print(f"COPIED_IMAGES: {len(copied)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Step 7 figure_index.json from a Zotero MinerU ZIP cache.")
    parser.add_argument("--zip", required=True, dest="zip_path", help="Path to LLM-for-Zotero-MinerU-cache-*.zip")
    parser.add_argument("--output", default="figure_index.json", help="Output figure_index.json path")
    parser.add_argument("--figures-dir", default="figures", help="Directory for selected/copied images")
    parser.add_argument("--copy-images", action="store_true", help="Copy all manifest figures into --figures-dir")
    args = parser.parse_args()

    return scan_mineru_zip(
        zip_path=Path(args.zip_path).expanduser().resolve(),
        output=Path(args.output).expanduser(),
        figures_dir=Path(args.figures_dir).expanduser() if args.figures_dir else None,
        copy_images=args.copy_images,
    )


if __name__ == "__main__":
    raise SystemExit(main())
