from yuanbao_exporter.parser import format_timestamp


def test_formats_minute_and_hour_timestamps() -> None:
    assert format_timestamp(50) == "00:00"
    assert format_timestamp(70_560) == "01:10"
    assert format_timestamp(3_662_000) == "01:01:02"

