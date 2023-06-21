from urllib.parse import urljoin, urlsplit
import argparse

from bs4 import BeautifulSoup
from pathlib import Path
from loguru import logger

import requests
from pathvalidate import sanitize_filename

from time import sleep


def save_to_file(url_content, path_to_file: Path):
    with open(path_to_file, "wb") as file:
        file.write(url_content.content)


def download_txt(url, filename, folder="books/"):
    folder_path = Path.cwd() / folder
    Path.mkdir(folder_path, exist_ok=True)
    file_path = Path(folder_path, sanitize_filename(filename))
    file_id = filename.split(".")[0]
    payload = {"id": file_id}

    response = requests.get(url, payload)
    response.raise_for_status()

    save_to_file(response, file_path)

    return file_path


def download_image(book_img_url: str, filename, folder="images/"):
    folder_path = Path.cwd() / folder
    Path.mkdir(folder_path, exist_ok=True)
    file_path = Path(folder_path, sanitize_filename(filename))

    response = requests.get(book_img_url)
    response.raise_for_status()

    save_to_file(response, file_path)

    return file_path


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError()


def parse_book_page(soup):
    author = soup.select_one(".ow_px_td h1").text.split("::")[1].strip()
    title = soup.select_one(".ow_px_td h1").text.split("::")[0].strip()
    genre = soup.select_one("span.d_book").text.split(":")[1].strip()
    book_img_url = soup.select_one(".bookimage img")["src"]
    book_img_name = urlsplit(book_img_url).path.split("/")[-1]

    raw_comments = soup.select(".texts")
    comments = [comment.select_one(".black").text for comment in raw_comments]

    book = {
        "author": author,
        "title": title,
        "genre": genre,
        "image_name": book_img_name,
        "image_url": book_img_url,
        "comments": comments,
    }

    return book


def download_book(url: str, book_id: int):
    txt_file_url = urljoin(url, "txt.php")

    book_page_response = requests.get(urljoin(url, f"b{book_id}/"))
    book_page_response.raise_for_status()
    check_for_redirect(book_page_response)
    soup = BeautifulSoup(book_page_response.text, "lxml")

    book = parse_book_page(soup)

    filename = "{}. {}.txt".format(book_id, sanitize_filename(book["title"]).strip())

    download_txt(txt_file_url, filename)
    download_image(urljoin(url, book["image_url"]), book["image_name"])

    logger.info(f"Book genre: {book['genre']}")

    if book["comments"]:
        for comment_number, comment in enumerate(book["comments"]):
            logger.info(f"Comment number: {comment_number + 1}. {comment}")

    return book


def main():
    parser = argparse.ArgumentParser(
        description="Download books from library tululu.org"
    )
    parser.add_argument(
        "start_id",
        type=int,
        help="Start book id.",
    )
    parser.add_argument(
        "end_id",
        type=int,
        help="End book id.",
    )
    args = parser.parse_args()

    for book_id in range(args.start_id, args.end_id + 1):
        url = f"https://tululu.org/"
        book = {}
        seconds_to_sleep = 5
        try_count = 0

        logger.info(f"Try to download book by link {url}b{book_id}/")
        while True:
            try:
                book = download_book(url, book_id)
            except requests.HTTPError:
                logger.warning("There is not ok response found. Skip the page.")
                break
            except requests.ConnectionError:
                if try_count > 0:
                    seconds_to_sleep = 20
                elif try_count >= 5:
                    logger.error(
                        f"Can't process the book {url}b{book_id}/ after 5 tries. Skip book."
                    )
                    break

                logger.warning(
                    f"There is no internet connection to server. "
                    f"Another try after sleep {seconds_to_sleep}."
                )

                sleep(seconds_to_sleep)
                try_count += 1
            else:
                break

        try:
            logger.info(f"File {book['title']} saved successfully.")
        except KeyError:
            logger.warning("Book was not download.")


if __name__ == "__main__":
    main()
