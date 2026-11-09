import io
import urllib.error

import pytest

import import_json_parallel as m


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(m.time, "sleep", lambda s: None)


def test_parse_date_formats():
    assert m.parse_date({"Date": "2026-11-01 12:00:00 UTC"}).year == 2026
    assert m.parse_date({"created": "2015-03-05"}).month == 3
    assert m.parse_date({"Date": "garbage"}) is None
    assert m.parse_date({}) is None


def test_target_folder(tmp_path):
    dt = m.parse_date({"Date": "2026-11-01 12:00:00 UTC"})
    assert m.get_target_folder(str(tmp_path), dt) == str(tmp_path / "2026" / "November")
    assert m.get_target_folder(str(tmp_path), None) == str(tmp_path / "Unsorted")


def test_fetch_success_atomic(tmp_path, monkeypatch):
    monkeypatch.setattr(m.urllib.request, "urlopen", lambda *a, **k: FakeResp(b"data"))
    dest = tmp_path / "a.jpg"
    m.fetch_to_file("https://x/a", str(dest))
    assert dest.read_bytes() == b"data"
    assert not (tmp_path / "a.jpg.part").exists()


def test_fetch_rejects_http(tmp_path):
    with pytest.raises(ValueError):
        m.fetch_to_file("http://x/a", str(tmp_path / "a.jpg"))


def test_fetch_404_no_retry(tmp_path, monkeypatch):
    calls = []

    def fake(*a, **k):
        calls.append(1)
        raise urllib.error.HTTPError("u", 404, "nf", {}, None)

    monkeypatch.setattr(m.urllib.request, "urlopen", fake)
    with pytest.raises(urllib.error.HTTPError):
        m.fetch_to_file("https://x/a", str(tmp_path / "a.jpg"))
    assert len(calls) == 1
    assert not (tmp_path / "a.jpg").exists()


def test_fetch_retries_500_then_ok(tmp_path, monkeypatch):
    calls = []

    def fake(*a, **k):
        calls.append(1)
        if len(calls) < 3:
            raise urllib.error.HTTPError("u", 500, "err", {}, None)
        return FakeResp(b"ok")

    monkeypatch.setattr(m.urllib.request, "urlopen", fake)
    m.fetch_to_file("https://x/a", str(tmp_path / "a.jpg"))
    assert len(calls) == 3
    assert (tmp_path / "a.jpg").read_bytes() == b"ok"


def test_download_item_creates_missing_year_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(m.urllib.request, "urlopen", lambda *a, **k: FakeResp(b"x"))
    item = {
        "Date": "2026-11-01 12:00:00 UTC",
        "Media Type": "Image",
        "Media Download Url": "https://x/a",
    }
    name, status, *_ = m.download_item(item, 1, set(), str(tmp_path), 1)
    assert status == "ok"
    assert (tmp_path / "2026" / "November" / "00001.jpg").exists()


def test_download_item_skips_existing(tmp_path):
    item = {"Media Type": "Image", "Media Download Url": "https://x/a"}
    _, status, *_ = m.download_item(item, 1, {"00001.jpg"}, str(tmp_path), 1)
    assert status == "skipped"
