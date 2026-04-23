from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.runners import run_ablation_eval


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compara configuraciones de retrieval.")
    parser.add_argument(
        "--dataset",
        default=os.getenv("EVAL_DATASET_PATH", "evaluation/datasets/rag_eval_questions.json"),
    )
    parser.add_argument(
        "--output-dir",
        default=os.getenv("EVAL_OUTPUT_DIR", "evaluation/reports"),
    )
    parser.add_argument(
        "--provider",
        choices=("mock", "openai", "openai_compatible"),
        default=os.getenv("EVAL_PROVIDER", "mock"),
    )
    parser.add_argument("--retrieval-only", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = run_ablation_eval(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        provider_name=args.provider,
        include_answer_eval=not args.retrieval_only,
    )
    paths = report.get("report_paths", {})
    print(f"Reporte JSON: {paths.get('json', '')}")
    print(f"Reporte Markdown: {paths.get('markdown', '')}")
    print(f"Best config: {report['summary']['Best config']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
