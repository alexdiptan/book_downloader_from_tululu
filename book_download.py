from bs4 import BeautifulSoup
from pathlib import Path
from loguru import logger

import requests
from pathvalidate import sanitize_filename


def save_book_to_file(url_content, path_to_file: Path):
    with open(path_to_file, "wb") as file:
        file.write(url_content.content)


def download_txt(url, filename, folder="books/"):
    folder_path = Path.cwd() / folder

    if not Path(folder_path).exists():
        Path.mkdir(folder_path)

    file_path = Path(folder_path, sanitize_filename(filename))

    url_response = get_url_response(url)

    save_book_to_file(url_response, file_path)

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
        book_page_url = f"{url}b{book_id}"
        logger.info(f"Try to download book from page - {book_page_url}")

        try:
            url_response = get_url_response(book_page_url)
        except requests.HTTPError:
            logger.warning("Redirect url found. Skip page.")
            continue

        soup = BeautifulSoup(url_response.text, "lxml")

        book_title, author = soup.find("body").find("h1").text.split("::")
        filename = "{}. {}.txt".format(book_id, sanitize_filename(book_title).strip())
        book_urls = soup.find(class_="d_book").find_all("a")

        txt_book_url = ""
        for book_url in book_urls:
            if book_url.text == "скачать txt":
                txt_book_url = f"{url}{book_url['href']}"
                continue

        if len(txt_book_url) < 1:
            logger.warning("Book page does not contain txt link. Skip book.")
            continue

        download_txt(txt_book_url, filename)

        logger.info(f"File {filename} saved successfully.")


if __name__ == "__main__":
    main()
