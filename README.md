# Парсер книг с сайта tululu.org
Скрипт скачивает книги с сайта [tululu.org](tululu.org).

## Как установить
Для корректной работы скрипта, необходимо последовательно выполнить команды:
```
git clone https://github.com/alexdiptan/book_downloader_from_tululu.git
cd book_downloader_from_tululu
python3 -m venv my_env
source my_env/bin/activate
pip3 install -r requirements.txt
```

## Аргументы
Скрипт принимает на вход начальный и конечный id книги.
Пример запуска скрипта: 
```
python3 main.py 1 3
```
Выполнив команду выше, будут скачаны книги с 1 по 3 включительно.

## Цель проекта
Код написан в образовательных целях на онлайн-курсе для веб-разработчиков dvmn.org.