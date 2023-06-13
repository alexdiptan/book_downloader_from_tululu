from urllib.parse import urljoin, urlsplit, urlparse, unquote

from bs4 import BeautifulSoup
from pathlib import Path
from loguru import logger

import requests
from pathvalidate import sanitize_filename


def save_to_file(url_content, path_to_file: Path):
    with open(path_to_file, "wb") as file:
        file.write(url_content.content)


def get_folder_path(folder_name: str) -> Path:
    folder_path = Path.cwd() / folder_name

    if not Path(folder_path).exists():
        Path.mkdir(folder_path)

    return folder_path


def download_txt(url, filename, folder="books/"):
    folder_path = get_folder_path(folder)

    file_path = Path(folder_path, sanitize_filename(filename))

    url_response = get_url_response(url)

    save_to_file(url_response, file_path)

    return file_path


def download_image(book_img_url: str, filename: str, folder="images/"):
    folder_path = get_folder_path(folder)
    file_path = Path(folder_path, sanitize_filename(filename))

    url_response = get_url_response(book_img_url)

    save_to_file(url_response, file_path)

    return file_path


def get_url_response(url: str):
    response = requests.get(url)
    response.raise_for_status()

    if len(response.history) > 1:
        raise requests.HTTPError()

    return response


def main():
    url = "https://tululu.org/"

    for book_id in range(1, 11):
        book_page_url = urljoin(url, f"b{book_id}")
        logger.info(f"Try to download book from page - {book_page_url}")

        try:
            url_response = get_url_response(book_page_url)
        except requests.HTTPError:
            logger.warning("Redirect url found. Skip page.")
            continue

        soup = BeautifulSoup(url_response.text, "lxml")

        book_title, author = soup.find("body").find("h1").text.split("::")
        filename = "{}. {}.txt".format(book_id, sanitize_filename(book_title).strip())
        book_info = soup.find(class_="d_book")
        book_urls = book_info.find_all("a")
        book_img_url = urljoin(url, book_info.find('img')['src'])
        book_img_name = urlsplit(book_img_url).path.split('/')[-1]

        txt_book_url = ""
        for book_url in book_urls:
            if book_url.text == "скачать txt":
                txt_book_url = f'{url}{book_url["href"]}'
                continue

        if len(txt_book_url) < 1:
            logger.warning("Book page does not contain txt link. Skip book.")
            continue

        # download_txt(txt_book_url, filename)
        download_image(book_img_url, book_img_name)

        logger.info(f"File {filename} saved successfully.")


if __name__ == "__main__":
    main()