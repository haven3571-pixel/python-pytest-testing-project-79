import os
from pathlib import Path
import logging
import bs4
import pytest
import requests
import requests_mock
from page_loader import download
from page_loader.naming import naming
import sys, subprocess



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


@pytest.mark.parametrize("status_code", [404, 500])
def test_download_http_errors(tmp_path, caplog, status_code):
    caplog.set_level(logging.ERROR)
    with requests_mock.Mocker() as m:
        m.get("https://ru.hexlet.io/courses", status_code=status_code)
        with pytest.raises(requests.exceptions.HTTPError):
            download("https://ru.hexlet.io/courses", tmp_path)

    assert any(record.levelname == "ERROR" for record in caplog.records)


def test_download_connection_error(tmp_path, caplog):
    caplog.set_level(logging.ERROR)
    with requests_mock.Mocker() as m:
        m.get("https://ru.hexlet.io/courses", exc=requests.exceptions.ConnectionError)
        with pytest.raises(requests.exceptions.RequestException):
            download("https://ru.hexlet.io/courses", tmp_path)

    assert any(record.levelname == "ERROR" for record in caplog.records)


def test_download_directory_does_not_exist(caplog):
    caplog.set_level(logging.ERROR)
    with pytest.raises(OSError):
        download("https://ru.hexlet.io/courses", "/path/to/non_existent_dir_12345")

    assert any(record.levelname == "ERROR" for record in caplog.records)


def test_download_target_is_file(tmp_path, caplog):
    caplog.set_level(logging.ERROR)
    with requests_mock.Mocker() as m:
        m.get("https://ru.hexlet.io/courses", text="<html></html>")
        fake_file = tmp_path / "hd.txt"
        fake_file.touch()

        with pytest.raises(OSError):
            download("https://ru.hexlet.io/courses", fake_file)

    assert any(record.levelname == "ERROR" for record in caplog.records)
    
    
def test_download_asset_error(tmp_path, caplog):
    caplog.set_level(logging.ERROR)
    with requests_mock.Mocker() as m:
        # Главная страница загрузилась успешно
        m.get("https://ru.hexlet.io/courses", text=read_file("before.html", "r"))
        
        # Но один из ее ресурсов падает с ошибкой (например, 404 или 500)
        m.get("https://ru.hexlet.io/assets/professions/python.png", status_code=404)
        m.get("https://ru.hexlet.io/assets/application.css", text="")
        m.get("https://ru.hexlet.io/packs/js/runtime.js", text="")

        with pytest.raises(requests.exceptions.RequestException):
            download("https://ru.hexlet.io/courses", tmp_path)

    # Проверяем, что в логе зафиксирована ошибка
    assert any(record.levelname == "ERROR" for record in caplog.records)
    
    
def test_cli_exit_code_error(tmp_path):
    result = subprocess.run(
        [
            "page-loader",
            "https://ru.hexlet.io/courses",
            "-o",
            str(tmp_path / "non_existent_folder_123"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert result.stderr != ""