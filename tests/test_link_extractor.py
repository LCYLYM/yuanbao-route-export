from yuanbao_exporter.link_extractor import extract_yuanbao_links


def test_extracts_unique_yuanbao_recording_links() -> None:
    source = """
    CROSS: 06-08 19:14:00
    点击查看元宝录音与总结内容
    https://yuanbao.tencent.com/e/rm/00000000-0000-4000-8000-000000000001

    CROSS: 06-08 19:14:18
    点击查看元宝录音与总结内容
    https://yuanbao.tencent.com/e/rm/00000000-0000-4000-8000-000000000002

    CROSS: 06-08 19:14:31
    点击查看元宝录音与总结内容
    https://yuanbao.tencent.com/e/rm/00000000-0000-4000-8000-000000000003
    """

    assert extract_yuanbao_links(source) == [
        "https://yuanbao.tencent.com/e/rm/00000000-0000-4000-8000-000000000001",
        "https://yuanbao.tencent.com/e/rm/00000000-0000-4000-8000-000000000002",
        "https://yuanbao.tencent.com/e/rm/00000000-0000-4000-8000-000000000003",
    ]
