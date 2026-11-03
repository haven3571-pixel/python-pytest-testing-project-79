from page_loader.naming import naming
import requests
import os


def download(url, path):
    file_name = naming(url)
    request = requests.get(url)
    path_final = os.path.join(path, file_name)
    with open(path_final, "w", encoding="utf-8") as f:
        f.write(request.text)
    return path_final