from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CODES_DIR = Path(__file__).resolve().parent
PLOT_SCRIPT = CODES_DIR / "tfnet" / "figure" / "plot_enhanced.py"
DATA_DIR = CODES_DIR / "tfnet" / "figure" / "data"
OUTPUT_ROOT = CODES_DIR / "demo_outputs"


@dataclass(frozen=True)
class DemoVideo:
    dataset: str
    video_name: str
    output_name: str
    polish: bool = False


DEFAULT_OUTPUT_NAMES = {
    ("summe", "St_Maarten_Landing"): "method1_results_visualization_St_Maarten_Landing.pdf",
    ("tvsum", "uGu_10sucQo"): "method1_results_visualization_uGu_10sucQo.pdf",
    ("summe", "playing_ball"): "method1_results_visualization_playing_ball.pdf",
    ("tvsum", "WxtbjNsCQ8A"): "method1_results_visualization_WxtbjNsCQ8A.pdf",
}

DEFAULT_VIDEOS = (
    DemoVideo(
        dataset="summe",
        video_name="St_Maarten_Landing",
        output_name=DEFAULT_OUTPUT_NAMES[("summe", "St_Maarten_Landing")],
        polish=False,
    ),
    DemoVideo(
        dataset="tvsum",
        video_name="uGu_10sucQo",
        output_name=DEFAULT_OUTPUT_NAMES[("tvsum", "uGu_10sucQo")],
        polish=False,
    ),
)


def normalize_video_name(video_name: str) -> str:
    return video_name.strip().replace(" ", "_")


def parse_video_specs(
    values: list[str] | None,
    polish_summe: bool = False,
) -> list[DemoVideo]:
    if not values:
        if not polish_summe:
            return list(DEFAULT_VIDEOS)
        return [
            DemoVideo(
                dataset=spec.dataset,
                video_name=spec.video_name,
                output_name=spec.output_name,
                polish=(spec.dataset == "summe"),
            )
            for spec in DEFAULT_VIDEOS
        ]

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
            f"method1_results_visualization_{video_name}.pdf",
        )
        specs.append(
            DemoVideo(
                dataset=dataset,
                video_name=video_name,
                output_name=output_name,
                polish=(polish_summe and dataset == "summe"),
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


def validate_data_files(specs: list[DemoVideo]) -> None:
    missing_paths = []
    for spec in specs:
        data_path = DATA_DIR / spec.dataset / f"{spec.video_name}.json"
        if not data_path.exists():
            missing_paths.append(data_path)

    if missing_paths:
        missing_text = "\n".join(f"  - {path}" for path in missing_paths)
        raise FileNotFoundError(
            "Missing Chapter 3 visualization data JSON files:\n"
            f"{missing_text}\n"
            "If you need to rebuild them, run tfnet/figure/build_figure_data.py first."
        )


def run_plot(spec: DemoVideo, output_dir: Path) -> Path:
    output_path = output_dir / spec.output_name
    command = [
        sys.executable,
        str(PLOT_SCRIPT),
        spec.dataset,
        spec.video_name,
        "--out",
        str(output_path),
    ]
    if spec.polish:
        command.append("--polish")

    print(f"[run] {shlex.join(command)}")
    subprocess.run(command, check=True)
    return output_path


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Chapter 3 visualization PDFs for live demo use."
    )
    parser.add_argument(
        "--video",
        action="append",
        default=None,
        help="Video spec in dataset:video_name format. Repeat to render multiple videos.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_ROOT / "chapter3_visualization"),
        help="Preferred output directory under Codes. If it already contains files, a new sibling directory is created automatically.",
    )
    parser.add_argument(
        "--polish-summe",
        action="store_true",
        help="Explicitly enable the cosmetic polish used by plot_enhanced.py for SumMe videos. Disabled by default so the final-score curve stays close to the raw sequence.",
    )
    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    if not PLOT_SCRIPT.exists():
        raise FileNotFoundError(f"Cannot find plot script: {PLOT_SCRIPT}")

    specs = parse_video_specs(args.video, polish_summe=args.polish_summe)
    validate_data_files(specs)

    output_dir = prepare_output_dir(Path(args.output_dir))
    print(f"Output directory: {output_dir}")

    generated_files = [run_plot(spec, output_dir) for spec in specs]

    print("Generated files:")
    for path in generated_files:
        print(f"  - {path}")


if __name__ == "__main__":
    main()