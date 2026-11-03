import os, argparse
from page_loader import download


def main():
    parser = argparse.ArgumentParser(description=
                                "Page downloader")
    parser.add_argument("url")
    parser.add_argument("-o", "--output",
                        default=os.getcwd(),
                        help="output directory")
    args = parser.parse_args()
    path = download(args.url, args.output)
    print(path) 


if __name__ == "main":
    main()