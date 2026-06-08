from yuanbao_exporter.export_service import MarkdownDocument
from yuanbao_exporter.markdown import render_single_markdown
from yuanbao_exporter.models import RecordingExport, TranscriptLine


def test_single_markdown_uses_recording_title_and_plain_transcript() -> None:
    recording = RecordingExport(
        url="https://yuanbao.tencent.com/e/rm/00000000-0000-4000-8000-000000000001",
        title="贝叶斯公式与概率计算讲解",
        summary="总结内容",
        transcript=[
            TranscriptLine(speaker="教师", timestamp="00:00", text="第一句。"),
            TranscriptLine(speaker="学生", timestamp="00:03", text="第二句。"),
        ],
    )

    markdown = render_single_markdown(recording, mode="plain-text")

    assert markdown.startswith("# 贝叶斯公式与概率计算讲解")
    assert "来源：https://yuanbao.tencent.com/e/rm/00000000-0000-4000-8000-000000000001" in markdown
    assert "总结内容" in markdown
    assert "第一句。\n第二句。" in markdown
    assert "教师 00:00" not in markdown


def test_markdown_document_is_filename_content_pair() -> None:
    document = MarkdownDocument(filename="01-test.md", content="# test\n")

    assert document.filename == "01-test.md"
    assert document.content == "# test\n"
