import pytest, os
from page_loader.naming import naming
import requests, requests_mock
from page_loader import download
from pathlib import Path



def read_file(name, mode):
    file_path = Path(__file__).parent / "fixtures" / name
    if mode == "r":
        return file_path.read_text(encoding="utf-8")
    elif mode == "rb":
        return file_path.read_bytes()



def test_naming():
    assert naming("https://ru.hexlet.io/courses") == "ru-hexlet-io-courses_files"
    assert naming("http://ru.hexlet.io/courses") == "ru-hexlet-io-courses_files"


def test_download(tmp_path):
    with requests_mock.Mocker() as m:
        m.get(
            "https://ru.hexlet.io/courses",
            text=read_file(
                "before.html", "r"
            )
        )
        m.get(
                "https://ru.hexlet.io/assets/professions/python.png",
                content=read_file(
                "python.png", "rb"
            )
        )
        path = download("https://ru.hexlet.io/courses", tmp_path) 
        assert path == os.path.join(tmp_path, "ru-hexlet-io-courses.html")
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert html == read_file("after.html", "r")
        assert os.path.exists(tmp_path / "ru-hexlet-io-courses_files")
        with open(os.path.join(tmp_path, "ru-hexlet-io-courses_files", "ru-hexlet-io-assets-professions-python.png"), "rb") as f:
            bytes = f.read()
        assert bytes == read_file("python.png", "rb")
        

