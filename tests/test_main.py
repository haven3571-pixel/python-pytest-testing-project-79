import logging
import pytest
import requests
import requests_mock
from page_loader import download


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