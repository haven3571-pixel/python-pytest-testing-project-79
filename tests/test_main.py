import os
from pathlib import Path
import logging
import bs4
import pytest
import requests
import requests_mock
from page_loader import download
from page_loader.naming import naming


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
        m.get("https://ru.hexlet.io/courses", text=read_file("before.html", "r"))
        m.get(
            "https://ru.hexlet.io/assets/professions/python.png",
            content=read_file("python.png", "rb"),
        )
        m.get(
            "https://ru.hexlet.io/assets/application.css",
            text=read_file("styles.css", "r"),
        )
        m.get(
            "https://ru.hexlet.io/packs/js/runtime.js", text=read_file("script.js", "r")
        )
        path = download("https://ru.hexlet.io/courses", tmp_path)
        assert path == os.path.join(tmp_path, "ru-hexlet-io-courses.html")
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        html_soup = bs4.BeautifulSoup(html, "html.parser")
        after_soup = bs4.BeautifulSoup(read_file("after.html", "r"), "html.parser")
        assert html_soup.prettify() == after_soup.prettify()
        assert os.path.exists(tmp_path / "ru-hexlet-io-courses_files")
        with open(
            os.path.join(
                tmp_path,
                "ru-hexlet-io-courses_files",
                "ru-hexlet-io-assets-professions-python.png",
            ),
            "rb",
        ) as f:
            bytes_data = f.read()
        assert bytes_data == read_file("python.png", "rb")
        with open(
            os.path.join(
                tmp_path,
                "ru-hexlet-io-courses_files",
                "ru-hexlet-io-packs-js-runtime.js",
            ),
            "r",
            encoding="utf-8",
        ) as f:
            js = f.read()
        assert js == read_file("script.js", "r")
        with open(
            os.path.join(
                tmp_path,
                "ru-hexlet-io-courses_files",
                "ru-hexlet-io-assets-application.css",
            ),
            "r",
            encoding="utf-8",
        ) as f:
            css = f.read()
        assert css == read_file("styles.css", "r")


def test_logging(tmp_path, caplog):
    caplog.set_level(logging.DEBUG)
    with requests_mock.Mocker() as m:
        m.get("https://ru.hexlet.io/courses", text=read_file("before.html", "r"))
        m.get(
            "https://ru.hexlet.io/assets/professions/python.png",
            content=read_file("python.png", "rb"),
        )
        m.get(
            "https://ru.hexlet.io/assets/application.css",
            text=read_file("styles.css", "r"),
        )
        m.get(
            "https://ru.hexlet.io/packs/js/runtime.js", text=read_file("script.js", "r")
        )
        download("https://ru.hexlet.io/courses", tmp_path)
        assert "Функция download начала работу" in caplog.text
        assert "Функция download закончила работу" in caplog.text
        assert "Записали содержимое тега img" in caplog.text
        assert "Записали содержимое тега script" in caplog.text
        assert "Записали содержимое тега link" in caplog.text
        assert "Главная страница сохранена" in caplog.text


def test_logging_failure(tmp_path, caplog):
    # 1. HTTP 404
    with requests_mock.Mocker() as m:
        m.get("https://ru.hexlet.io/courses", status_code=404)
        with pytest.raises(requests.exceptions.HTTPError):
            download("https://ru.hexlet.io/courses", tmp_path)

    assert any(record.levelname == "ERROR" for record in caplog.records)
    caplog.clear()

    # 2. Ошибка подключения (ConnectionError - сетевой сбой)
    with requests_mock.Mocker() as m:
        m.get("https://ru.hexlet.io/courses", exc=requests.exceptions.ConnectionError)
        with pytest.raises(requests.exceptions.ConnectionError):
            download("https://ru.hexlet.io/courses", tmp_path)

    assert any(record.levelname == "ERROR" for record in caplog.records)
    caplog.clear()

    # 3. Файловая ошибка (передан существующий файл вместо директории)
    with requests_mock.Mocker() as m:
        m.get("https://ru.hexlet.io/courses", text="<html></html>")
        fake_dir = tmp_path / "hd.txt"
        fake_dir.touch()

        with pytest.raises(OSError):
            download("https://ru.hexlet.io/courses", fake_dir)

    assert any(record.levelname == "ERROR" for record in caplog.records)