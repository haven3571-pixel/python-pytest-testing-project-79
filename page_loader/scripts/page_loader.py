import os, argparse, logging, sys, requests
from page_loader import download


logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser(description=
                                "Page downloader")
    parser.add_argument("url")
    parser.add_argument("-o", "--output",
                        default=os.getcwd(),
                        help="output directory")
    args = parser.parse_args()
    try:
        path = download(args.url, args.output)
        print(path) 
    except (requests.RequestException, OSError) as error:
        logging.error(f"Error: {error}")
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()