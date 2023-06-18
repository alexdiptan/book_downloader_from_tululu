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

    url_response = get_url_response(url)

    save_to_file(url_response, file_path)

    return file_path


def download_image(book_img_url: str, filename, folder="images/"):
    folder_path = Path.cwd() / folder
    Path.mkdir(folder_path, exist_ok=True)
    file_path = Path(folder_path, sanitize_filename(filename))

    url_response = get_url_response(book_img_url)

    save_to_file(url_response, file_path)

    return file_path


def get_url_response(url: str):
    response = requests.get(url)
    response.raise_for_status()

    return response


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError()


def get_comments(soup):
    raw_comments = soup.select(".texts")
    comments = [comment.select_one(".black").text for comment in raw_comments]

    return comments


def get_title(soup):
    title = soup.select_one(".ow_px_td h1").text.split("::")

    return title[0].strip()


def get_author(soup):
    author = soup.select_one(".ow_px_td h1").text.split("::")

    return author[1].strip()


def get_genre(soup):
    genre = soup.select_one("span.d_book").text.split(":")[1].strip()

    return genre.strip()


def get_book_image(soup):
    book_img_url = soup.select_one(".bookimage img")["src"]

    return book_img_url


def parse_book_page(soup):
    book_img_url = get_book_image(soup)
    book_img_name = urlsplit(book_img_url).path.split("/")[-1]

    book = {
        "author": get_author(soup),
        "title": get_title(soup),
        "genre": get_genre(soup),
        "image_name": book_img_name,
        "image_url": book_img_url,
        "comments": get_comments(soup),
    }

    return book


def book_download(book_url: str, book_id: int):
    txt_file_url = urljoin(book_url, f'txt.php?id={book_id}')

    book_file_response = get_url_response(txt_file_url)
    check_for_redirect(book_file_response)

    book_page_response = get_url_response(book_url)
    soup = BeautifulSoup(book_page_response.text, "lxml")

    book = parse_book_page(soup)

    filename = "{}. {}.txt".format(
        book_id, sanitize_filename(book['title']).strip()
    )

    download_txt(txt_file_url, filename)
    download_image(urljoin(book_url, book["image_url"]), book["image_name"])

    logger.info(f"Book genre: {book['genre']}")

    if book["comments"]:
        for comment_number, comment in enumerate(book["comments"]):
            logger.info(f"Comment number: {comment_number + 1}. {comment}")

    return book


def main():
    parser = argparse.ArgumentParser(description='Download books from library tululu.org')
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

    for book_id in range(args.start_id, args.end_id+1):
        base_url = f"https://tululu.org/b{book_id}"
        book = {}
        seconds_to_sleep = 5
        try_count = 0

        logger.info(f"Try to download book by link {base_url}")
        while True:
            try:
                book = book_download(base_url, book_id)
            except requests.HTTPError:
                logger.warning("There is not ok response found. Skip the page.")
                break
            except requests.ConnectionError:
                if try_count > 0:
                    seconds_to_sleep = 20
                elif try_count >= 5:
                    logger.error(f"Can't process the book {base_url} after 5 tries. Skip book.")
                    break

                logger.warning(f"There is no internet connection to server. "
                               f"Another try after sleep {seconds_to_sleep}.")

                sleep(seconds_to_sleep)
                try_count += 1
            else:
                break

        if "title" not in book.keys():
            logger.warning('Book was not download.')
            continue

        logger.info(f"File {book['title']} saved successfully.")


if __name__ == "__main__":
    main()
