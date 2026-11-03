def naming(url: str):
    if url[-1] == "/":
        url = url[0:-1:1]
    url = url.replace("https://", "").replace("http://", "").replace("/", "-").replace(".", "-")
    url = url + ".html"
    return url