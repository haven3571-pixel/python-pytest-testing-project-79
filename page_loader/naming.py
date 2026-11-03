import os
from urllib.parse import urlparse, urljoin
import re


def naming(url: str):
    if url[-1] == "/":
        url = url[0:-1:1]
    url = url.replace("https://", "").replace("http://", "").replace("/", "-").replace(".", "-")
    url = url + "_files"
    return url


def url_to_filename(url, default_ext=".html"):
    parsed = urlparse(url)
    # Собираем путь без схемы (домен + путь)
    netloc_and_path = f"{parsed.netloc}{parsed.path}"
    
    # Отделяем корень пути от расширения (например: ('.../python', '.png'))
    root, ext = os.path.splitext(netloc_and_path)
    
    # Заменяем все небуквенно-цифровые символы на дефисы
    normalized_name = re.sub(r'[\W_]+', '-', root).strip('-')
    
    # Если расширения в URL не было (например, адрес страницы), берем default_ext
    final_ext = ext if ext else default_ext
    
    return f"{normalized_name}{final_ext}"