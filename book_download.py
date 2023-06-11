from pathlib import Path

import requests


def save_book_to_file(url_content, file_name: str, path_to_save: Path):
    with open(f"{path_to_save}/{file_name}", "wb") as file:
        file.write(url_content.content)


def main():
    url = "https://tululu.org/txt.php?id="
    book_path = Path.cwd() / "books"

    for book_id in range(1, 10):
        filename = f"id_{book_id}.txt"
        response = requests.get(url+str(book_id))
        response.raise_for_status()

        if not book_path.exists():
            Path.mkdir(book_path)

        save_book_to_file(response, filename, book_path)
        print(f"File {filename} saved successfully.")


if __name__ == '__main__':
    main()
