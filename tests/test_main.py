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


# 1. Сетевые ошибки: тестируем 404, 500 и обрыв сети раздельно через параметризацию
@pytest.mark.parametrize("status_code", [404, 500])
def test_download_http_errors(tmp_path, caplog, status_code):
    caplog.set_level(logging.ERROR)
    with requests_mock.Mocker() as m:
        m.get("https://ru.hexlet.io/courses", status_code=status_code)

        with pytest.raises(requests.exceptions.HTTPError):
            download("https://ru.hexlet.io/courses", tmp_path)

    assert any(record.levelname == "ERROR" for record in caplog.records)


# 2. Ошибка отсутствия директории (тест на non-existent path)
def test_download_directory_does_not_exist(caplog):
    caplog.set_level(logging.ERROR)
    non_existent_path = "/path/to/non_existent_folder_12345"

    with pytest.raises(OSError):
        download("https://ru.hexlet.io/courses", non_existent_path)

    assert any(record.levelname == "ERROR" for record in caplog.records)


# 3. Ошибка файловой системы (попытка записи внутрь файла)
def test_download_target_is_file(tmp_path, caplog):
    caplog.set_level(logging.ERROR)
    with requests_mock.Mocker() as m:
        m.get("https://ru.hexlet.io/courses", text="<html></html>")
        target_file = tmp_path / "file.txt"
        target_file.touch()

        with pytest.raises(OSError):
            download("https://ru.hexlet.io/courses", target_file)

    assert any(record.levelname == "ERROR" for record in caplog.records)