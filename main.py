from urllib.parse import urljoin, urlsplit
import argparse

from bs4 import BeautifulSoup
from pathlib import Path
from loguru import logger

import requests
from pathvalidate import sanitize_filename


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


def parse_book_page(soup):
    title, author = soup.find("body").find("h1").text.split("::")
    book_info = soup.find("table", class_="d_book")
    book_img_url = book_info.find("img")["src"]
    book_img_name = urlsplit(book_img_url).path.split("/")[-1]
    book_comments = soup.find_all(class_="texts")
    comments = [comment.find(class_="black").text for comment in book_comments]
    genre = soup.find("span", class_="d_book").text.split(":")[1].strip()

    book_data = {
        "author": author,
        "title": title,
        "genre": genre,
        "image_name": book_img_name,
        "image_url": book_img_url,
        "comments": comments,
    }

    return book_data


def book_download(base_url: str, book_id):
    txt_file_url = urljoin(base_url, f'txt.php?id={book_id}')
    book_page_url = urljoin(base_url, f"b{book_id}")

    book_file_response = get_url_response(txt_file_url)
    check_for_redirect(book_file_response)

    book_page_response = get_url_response(book_page_url)
    soup = BeautifulSoup(book_page_response.text, "lxml")

    book = parse_book_page(soup)

    filename = "{}. {}.txt".format(
        book_id, sanitize_filename(book['title']).strip()
    )

    download_txt(urljoin(base_url, txt_file_url), filename)
    download_image(urljoin(base_url, book["image_url"]), book["image_name"])

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
        base_url = "https://tululu.org/"

        logger.info(f"Try to download book id{book_id}")

        try:
            book = book_download(base_url, book_id)
        except requests.HTTPError:
            logger.warning("Redirect url found. Skip page.")
            continue

        logger.info(f"File {book['title']} saved successfully.")


if __name__ == "__main__":
    main()