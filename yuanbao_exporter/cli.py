from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .export_service import (
    ExportError,
    build_markdown_documents_from_input,
    build_markdown_from_input,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Yuanbao recording shares to Markdown.")
    parser.add_argument(
        "--mode",
        choices=("with-speakers", "plain-text"),
        default="with-speakers",
        help="Markdown transcript mode.",
    )
    parser.add_argument("--output", required=True, help="Output Markdown file path.")
    parser.add_argument(
        "--layout",
        choices=("combined", "separate"),
        default="combined",
        help="combined writes one Markdown file; separate writes one Markdown per link.",
    )
    parser.add_argument(
        "--proxy-url",
        default=os.environ.get("YUANBAO_PROXY_URL"),
        help="Optional HTTP proxy URL, for example http://127.0.0.1:8080.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw_input = sys.stdin.read()
    try:
        if args.layout == "separate":
            documents = build_markdown_documents_from_input(
                raw_input=raw_input,
                mode=args.mode,
                proxy_url=args.proxy_url,
            )
        else:
            markdown = build_markdown_from_input(
                raw_input=raw_input,
                mode=args.mode,
                proxy_url=args.proxy_url,
            )
    except ExportError as exc:
        print(f"export failed: {exc}", file=sys.stderr)
        return 1

    output_path = Path(args.output)
    if args.layout == "separate":
        if output_path.suffix.lower() == ".zip":
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
                for document in documents:
                    archive.writestr(document.filename, document.content)
        else:
            output_path.mkdir(parents=True, exist_ok=True)
            for document in documents:
                (output_path / document.filename).write_text(
                    document.content,
                    encoding="utf-8",
                )
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
