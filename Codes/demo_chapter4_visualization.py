from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CODES_DIR = Path(__file__).resolve().parent
PLOT_SCRIPT = CODES_DIR / "tfnet" / "figure" / "plot_enhanced_c4.py"
BUILD_DATA_SCRIPT = CODES_DIR / "tfnet" / "figure" / "build_figure_data_c4.py"
DATA_DIR = CODES_DIR / "tfnet" / "figure" / "data"
OUTPUT_ROOT = CODES_DIR / "demo_outputs"


@dataclass(frozen=True)
class DemoVideo:
    dataset: str
    video_name: str
    output_name: str


DEFAULT_OUTPUT_NAMES = {
    ("summe", "St_Maarten_Landing"): "method2_results_visualization_St_Maarten_Landing.pdf",
    ("tvsum", "uGu_10sucQo"): "method2_results_visualization_uGu_10sucQo.pdf",
    ("summe", "car_over_camera"): "top3_car_over_camera.pdf",
    ("tvsum", "qqR6AEXwxoQ"): "method2_results_visualization_qqR6AEXwxoQ.pdf",
}

DEFAULT_VIDEOS = (
    DemoVideo(
        dataset="summe",
        video_name="St_Maarten_Landing",
        output_name=DEFAULT_OUTPUT_NAMES[("summe", "St_Maarten_Landing")],
    ),
    DemoVideo(
        dataset="tvsum",
        video_name="uGu_10sucQo",
        output_name=DEFAULT_OUTPUT_NAMES[("tvsum", "uGu_10sucQo")],
    ),
)


def normalize_video_name(video_name: str) -> str:
    return video_name.strip().replace(" ", "_")


def parse_video_specs(values: list[str] | None) -> list[DemoVideo]:
    if not values:
        return list(DEFAULT_VIDEOS)

    specs: list[DemoVideo] = []
    for raw in values:
        if ":" not in raw:
            raise ValueError(
                f"Invalid --video value: {raw!r}. Expected dataset:video_name."
            )
        dataset, video_name = raw.split(":", 1)
        dataset = dataset.strip().lower()
        video_name = normalize_video_name(video_name)
        if dataset not in {"summe", "tvsum"}:
            raise ValueError(f"Unsupported dataset: {dataset}")
        if not video_name:
            raise ValueError(f"Empty video name in --video value: {raw!r}")

        output_name = DEFAULT_OUTPUT_NAMES.get(
            (dataset, video_name),
            f"method2_results_visualization_{video_name}.pdf",
        )
        specs.append(
            DemoVideo(
                dataset=dataset,
                video_name=video_name,
                output_name=output_name,
            )
        )
    return specs


def prepare_output_dir(target_dir: Path) -> Path:
    target_dir = target_dir.expanduser()
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    candidate = target_dir
    index = 0
    while True:
        if not candidate.exists():
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate
        if candidate.is_dir() and not any(candidate.iterdir()):
            return candidate
        index += 1
        candidate = target_dir.parent / f"{target_dir.name}_{index:02d}"


def run_command(command: list[str], label: str) -> None:
    print(f"[{label}] {shlex.join(command)}")
    subprocess.run(command, check=True)


def ensure_figure_data(
    specs: list[DemoVideo],
    suffix: str,
    config: str,
    rebuild_data: bool,
) -> None:
    if not BUILD_DATA_SCRIPT.exists():
        raise FileNotFoundError(f"Cannot find figure-data build script: {BUILD_DATA_SCRIPT}")

    for spec in specs:
        data_path = DATA_DIR / f"{spec.dataset}_{suffix}" / f"{spec.video_name}.json"
        if data_path.exists() and not rebuild_data:
            continue

        command = [
            sys.executable,
            str(BUILD_DATA_SCRIPT),
            spec.video_name,
            spec.dataset,
            "--config",
            config,
            "--suffix",
            suffix,
        ]
        run_command(command, label="build")

        if not data_path.exists():
            raise FileNotFoundError(f"Expected figure data was not created: {data_path}")


def run_plot(spec: DemoVideo, output_dir: Path, suffix: str) -> Path:
    output_path = output_dir / spec.output_name
    command = [
        sys.executable,
        str(PLOT_SCRIPT),
        spec.dataset,
        spec.video_name,
        "--suffix",
        suffix,
        "--out",
        str(output_path),
    ]
    run_command(command, label="run")
    return output_path


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Chapter 4 visualization PDFs for live demo use."
    )
    parser.add_argument(
        "--video",
        action="append",
        default=None,
        help="Video spec in dataset:video_name format. Repeat to render multiple videos.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_ROOT / "chapter4_visualization_32s"),
        help="Preferred output directory under Codes. If it already contains files, a new sibling directory is created automatically.",
    )
    parser.add_argument(
        "--suffix",
        default="c4_32s",
        help="Figure-data suffix. The default is fixed to the 32s Chapter 4 data.",
    )
    parser.add_argument(
        "--config",
        default="32s-deepseek",
        help="Archive config used when Chapter 4 figure data needs to be rebuilt.",
    )
    parser.add_argument(
        "--rebuild-data",
        action="store_true",
        help="Rebuild the Chapter 4 figure-data JSON files before plotting.",
    )
    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    if not PLOT_SCRIPT.exists():
        raise FileNotFoundError(f"Cannot find plot script: {PLOT_SCRIPT}")

    specs = parse_video_specs(args.video)
    ensure_figure_data(specs, args.suffix, args.config, args.rebuild_data)

    output_dir = prepare_output_dir(Path(args.output_dir))
    print(f"Output directory: {output_dir}")
    print(f"Using Chapter 4 data suffix: {args.suffix}")
    print(f"Using archive config: {args.config}")

    generated_files = [run_plot(spec, output_dir, args.suffix) for spec in specs]

    print("Generated files:")
    for path in generated_files:
        print(f"  - {path}")


if __name__ == "__main__":
    main()