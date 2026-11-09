import io
import urllib.error

import pytest

import import_json as m


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(m.time, "sleep", lambda s: None)


def test_fetch_success_atomic(tmp_path, monkeypatch):
    monkeypatch.setattr(m.urllib.request, "urlopen", lambda *a, **k: FakeResp(b"data"))
    dest = tmp_path / "a.jpg"
    m.fetch_to_file("https://x/a", str(dest))
    assert dest.read_bytes() == b"data"
    assert not (tmp_path / "a.jpg.part").exists()


def test_fetch_rejects_http(tmp_path):
    with pytest.raises(ValueError):
        m.fetch_to_file("http://x/a", str(tmp_path / "a.jpg"))


def test_fetch_retries_then_fails_cleanly(tmp_path, monkeypatch):
    calls = []

    def fake(*a, **k):
        calls.append(1)
        raise urllib.error.URLError("down")

    monkeypatch.setattr(m.urllib.request, "urlopen", fake)
    with pytest.raises(urllib.error.URLError):
        m.fetch_to_file("https://x/a", str(tmp_path / "a.jpg"))
    assert len(calls) == m.RETRIES
    assert not (tmp_path / "a.jpg.part").exists()
