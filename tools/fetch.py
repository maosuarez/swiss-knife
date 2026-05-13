import sys
import argparse
import requests
from bs4 import BeautifulSoup


def do_something(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    for script in soup(["script", "style"]):
        script.decompose()

    text = soup.get_text()
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def run():
    parser = argparse.ArgumentParser(description="Fetch web clean text")
    parser.add_argument("url")
    args = parser.parse_args()

    print(do_something(args.url))
