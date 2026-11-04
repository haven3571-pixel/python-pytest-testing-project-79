import os
import stat
from pathlib import Path
import logging
import bs4
import pytest
import requests
import requests_mock
from page_loader import download
from page_loader.naming import naming


def read_file(name, mode="r"):
    file_path = Path(__file__).parent / "fixtures" / name
    if mode == "r":
        return file_path.read_text(encoding="utf-8")
    return file_path.read_bytes()


def test_naming():
    assert naming("https://ru.hexlet.io/courses") == "ru-hexlet-io-courses_files"
    assert naming("http://ru.hexlet.io/courses") == "ru-hexlet-io-courses_files"


def test_download_success(tmp_path):
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
            "https://ru.hexlet.io/packs/js/runtime.js",
            text=read_file("script.js", "r"),
        )

        path = download("https://ru.hexlet.io/courses", tmp_path)
        assert path == os.path.join(tmp_path, "ru-hexlet-io-courses.html")
        assert os.path.exists(path)

        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        html_soup = bs4.BeautifulSoup(html, "html.parser")
        after_soup = bs4.BeautifulSoup(read_file("after.html", "r"), "html.parser")
        assert html_soup.prettify() == after_soup.prettify()

        assets_dir = tmp_path / "ru-hexlet-io-courses_files"
        assert os.path.exists(assets_dir)

        img_path = assets_dir / "ru-hexlet-io-assets-professions-python.png"
        assert img_path.read_bytes() == read_file("python.png", "rb")


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
            "https://ru.hexlet.io/packs/js/runtime.js",
            text=read_file("script.js", "r"),
        )
        download("https://ru.hexlet.io/courses", tmp_path)
        assert "Функция download начала работу" in caplog.text
        assert "Функция download закончила работу" in caplog.text


# 1. Проверка ошибок статус-кодов (404, 500)
@pytest.mark.parametrize("status_code", [404, 500])
def test_download_http_errors(tmp_path, caplog, status_code):
    caplog.set_level(logging.ERROR)
    with requests_mock.Mocker() as m:
        m.get("https://ru.hexlet.io/courses", status_code=status_code)
        with pytest.raises(requests.exceptions.HTTPError):
            download("https://ru.hexlet.io/courses", tmp_path)

    assert any(record.levelname == "ERROR" for record in caplog.records)


# 2. Проверка сетевого сбоя (ConnectionError / DNS error / unknown network error)
def test_download_connection_error(tmp_path, caplog):
    caplog.set_level(logging.ERROR)
    with requests_mock.Mocker() as m:
        m.get("https://ru.hexlet.io/courses", exc=requests.exceptions.ConnectionError)
        with pytest.raises(requests.exceptions.RequestException):
            download("https://ru.hexlet.io/courses", tmp_path)

    assert any(record.levelname == "ERROR" for record in caplog.records)


# 3. Проверка несуществующей директории
def test_download_directory_does_not_exist(caplog):
    caplog.set_level(logging.ERROR)
    with pytest.raises(OSError):
        download("https://ru.hexlet.io/courses", "/path/to/non_existent_folder_12345")

    assert any(record.levelname == "ERROR" for record in caplog.records)


# 4. Проверка записи в файл вместо каталога
def test_download_target_is_file(tmp_path, caplog):
    caplog.set_level(logging.ERROR)
    with requests_mock.Mocker() as m:
        m.get("https://ru.hexlet.io/courses", text="<html></html>")
        fake_file = tmp_path / "hd.txt"
        fake_file.touch()

        with pytest.raises(OSError):
            download("https://ru.hexlet.io/courses", fake_file)

    assert any(record.levelname == "ERROR" for record in caplog.records)


# 5. Проверка отсутствия прав на запись (PermissionError)
def test_download_permission_denied(tmp_path, caplog):
    caplog.set_level(logging.ERROR)
    read_only_dir = tmp_path / "read_only"
    read_only_dir.mkdir()
    read_only_dir.chmod(stat.S_IREAD | stat.S_IEXEC)

    try:
        with requests_mock.Mocker() as m:
            m.get("https://ru.hexlet.io/courses", text="<html></html>")
            with pytest.raises(OSError):
                download("https://ru.hexlet.io/courses", read_only_dir)

        assert any(record.levelname == "ERROR" for record in caplog.records)
    finally:
        read_only_dir.chmod(stat.S_IRWXU)