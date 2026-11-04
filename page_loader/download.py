import os
import urllib.parse
import bs4
import requests
import logging
from page_loader.naming import naming, url_to_filename


attrs_match = {
    "img": "src",
    "link": "href",
    "script": "src",
}


logger = logging.getLogger(__name__)


def is_local(page_url, asset_url):
    final_path = urllib.parse.urljoin(page_url, asset_url)
    final_path_parsed = urllib.parse.urlparse(final_path)
    page_url_parsed = urllib.parse.urlparse(page_url)
    return final_path_parsed.netloc == page_url_parsed.netloc


def download(url, path=None):
    
    if path is None:
        path = os.getcwd()
    
    if not os.path.isdir(path):
        logger.error("Папка не существует")
        raise OSError("Папка не существует")
    
    logger.info(f"Функция download начала работу по адресу {url}")
    folder_name = naming(url)
    file_name = url_to_filename(url)
    try:
        request = requests.get(url)
        request.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Проблема с доступом к {url}, ошибка: {e}")
        raise
    path_final = os.path.join(path, file_name)
    folder_path = os.path.join(path, folder_name)
    try:
        os.makedirs(folder_path, exist_ok=True)
    except OSError as e:
        logger.error(f"Не удалось создать директорию {folder_path}: {e}")
        raise

    html: bs4.BeautifulSoup = bs4.BeautifulSoup(request.text, "html.parser")

    for tag in html.find_all(["img", "script", "link"]):
        tag_attr = attrs_match.get(tag.name)
        
        if not tag.get(tag_attr):
            logger.debug(f"Атрибут {tag_attr} не был найден")
            continue
        
        asset_path = tag.get(tag_attr)
        
        if not is_local(url, asset_path):
            logger.debug(f"Атрибут {tag_attr} указывает на внешний ресурс, пропуск")
            continue
        
        asset_full_path = urllib.parse.urljoin(url, asset_path)
        asset_file_name = url_to_filename(asset_full_path)
        
        try:
            content = requests.get(asset_full_path)
            content.raise_for_status()
            content = content.content
        except requests.RequestException as e:
            logger.error(f"Не удалось скачать ресурс {asset_full_path}: {e}")
            raise
        
        local_path = os.path.join(path, folder_name, asset_file_name)
        
        tag[tag_attr] = os.path.join(folder_name, asset_file_name)
        
        try:
            with open(local_path, "wb") as f:
                logger.debug(f"Записали содержимое тега {tag.name}")
                f.write(content)
        except OSError as e:
            logger.error(f"Ошибка с файловой системой: {e}")
            raise
        
    try:
        with open(path_final, "w", encoding="utf-8") as f:
            logger.debug("Главная страница сохранена")
            f.write(html.prettify())
    except OSError as e:
            logger.error(f"Ошибка с файловой системой: {e}")
            raise
        
    logger.info("Функция download закончила работу")
    return path_final

