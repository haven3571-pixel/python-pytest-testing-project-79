import os
import urllib.parse
import bs4
import requests
from page_loader.naming import naming, url_to_filename


def download(url, path):
    folder_name = naming(url)
    file_name = folder_name.replace("_files", ".html")
    request = requests.get(url)

    path_final = os.path.join(path, file_name)
    folder_path = os.path.join(path, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    base_domain = urllib.parse.urlparse(url).netloc
    html: bs4.BeautifulSoup = bs4.BeautifulSoup(request.text, "html.parser")

    for img in html.find_all("img"):
        src = img.get("src")
        if not src:
            continue

        img_url = urllib.parse.urljoin(url, src)

        # Скачиваем только ресурсы с того же домена
        if urllib.parse.urlparse(img_url).netloc != base_domain:
            continue    
    
        img_url = urllib.parse.urljoin(url, src)
        img_domain = urllib.parse.urlparse(img_url).netloc
        
        print(f"SRC: {src}")
        print(f"  -> Итоговый URL: {img_url}")
        print(f"  -> Домен ресурса: {img_domain} | Домен страницы: {base_domain}")
        print(f"  -> Совпадают? {img_domain == base_domain}\n")

        img_name = url_to_filename(img_url)
        img["src"] = f"{folder_name}/{img_name}"

        img_bytes = requests.get(img_url).content
        with open(os.path.join(folder_path, img_name), "wb") as f:
            f.write(img_bytes)

    with open(path_final, "w", encoding="utf-8") as f:
        f.write(html.prettify())

    return path_final