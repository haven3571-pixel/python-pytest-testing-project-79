import pytest
from page_loader.naming import naming
import requests, requests_mock
from page_loader import download
from pathlib import Path
import os


@pytest.fixture
def read_file(name, mode):
    file_path = Path(__file__).parent / "fixtures" / name
    if mode == "r":
        return file_path.read_text(encoding="utf-8")
    elif mode == "rb":
        return file_path.read_bytes()




def test_naming():
    assert naming("https://ru.hexlet.io/courses") == "ru-hexlet-io-courses.html"
    assert naming("http://ru.hexlet.io/courses") == "ru-hexlet-io-courses.html"


def test_download(tmp_path, read_file):
    with requests_mock.Mocker() as m:
        m.get(
            "http://ru.hexlet.io/courses",
            text=read_file(
                Path(__file__).parent / "fixtures" / "after.html"
            ),
            content=read_file(
                Path(__file__).parent / "fixtures" / "python.png"
            )
        )
        path = download("http://ru.hexlet.io/courses", tmp_path) 
        assert path == tmp_path / "ru-hexlet-io-courses.html"
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert html == read_file(tmp_path, )

