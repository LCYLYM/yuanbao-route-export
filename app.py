from __future__ import annotations

import logging
import os
from io import BytesIO
from datetime import datetime
from urllib.parse import quote
from zipfile import ZIP_DEFLATED, ZipFile

from flask import Flask, Response, render_template, request
from werkzeug.utils import secure_filename

from yuanbao_exporter.export_service import (
    ExportError,
    build_markdown_documents_from_input,
    build_markdown_from_input,
)


MAX_INPUT_CHARS = 50_000
SUPPORTED_LAYOUTS = {"combined", "separate"}


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 256 * 1024

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.post("/export")
    def export() -> Response | str:
        raw_input = request.form.get("source_text", "")
        mode = request.form.get("mode", "with-speakers")
        layout = request.form.get("layout", "combined")
        proxy_url = request.form.get("proxy_url", "").strip() or None

        if len(raw_input) > MAX_INPUT_CHARS:
            return render_template(
                "index.html",
                error=f"输入过长，最多允许 {MAX_INPUT_CHARS} 个字符。",
                source_text=raw_input[:MAX_INPUT_CHARS],
                selected_mode=mode,
                selected_layout=layout,
                proxy_url=proxy_url or "",
            ), 400

        if layout not in SUPPORTED_LAYOUTS:
            return render_template(
                "index.html",
                error=f"不支持的导出组织方式：{layout}",
                source_text=raw_input,
                selected_mode=mode,
                selected_layout=layout,
                proxy_url=proxy_url or "",
            ), 400

        try:
            if layout == "separate":
                documents = build_markdown_documents_from_input(
                    raw_input=raw_input,
                    mode=mode,
                    proxy_url=proxy_url,
                )
            else:
                markdown = build_markdown_from_input(
                    raw_input=raw_input,
                    mode=mode,
                    proxy_url=proxy_url,
                )
        except ExportError as exc:
            app.logger.warning("export failed: %s", exc)
            return render_template(
                "index.html",
                error=str(exc),
                source_text=raw_input,
                selected_mode=mode,
                selected_layout=layout,
                proxy_url=proxy_url or "",
            ), 400

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = "with-speakers" if mode == "with-speakers" else "plain-text"
        if layout == "separate":
            zip_buffer = BytesIO()
            with ZipFile(zip_buffer, "w", compression=ZIP_DEFLATED) as archive:
                for document in documents:
                    archive.writestr(document.filename, document.content)
            filename = secure_filename(f"yuanbao-separate-{suffix}-{timestamp}.zip")
            disposition = (
                f"attachment; filename={filename}; "
                f"filename*=UTF-8''{quote(filename)}"
            )
            return Response(
                zip_buffer.getvalue(),
                content_type="application/zip",
                headers={"Content-Disposition": disposition},
            )

        filename = secure_filename(f"yuanbao-{suffix}-{timestamp}.md")
        disposition = (
            f"attachment; filename={filename}; "
            f"filename*=UTF-8''{quote(filename)}"
        )
        return Response(
            markdown,
            content_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": disposition},
        )

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(host="127.0.0.1", port=port, debug=False)
