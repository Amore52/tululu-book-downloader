import os
import requests
from bs4 import BeautifulSoup


def check_for_redirect(response):
    if response.history and response.url == "https://tululu.org/":
        raise requests.exceptions.HTTPError("Redirected to the homepage")


def get_book_details(book_id):
    url = f"https://tululu.org/b{book_id}/"
    response = requests.get(url)
    check_for_redirect(response)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('h1').get_text()
    return title


def download_txt(url, filename, book_id, folder='books/'):
    response = requests.get(url)
    response.raise_for_status()
    if 'text/plain' not in response.headers.get('Content-Type', ''):
        raise requests.exceptions.HTTPError("URL не ведет к текстовому файлу")
    if '<html>' in response.text.lower():
        raise requests.exceptions.HTTPError("Скачан HTML файл, а не текстовый файл")
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{book_id}. {filename}.txt")  # добавляем номер книги к имени файла
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def download_books():
    for book_id in range(1, 11):
        try:
            title = get_book_details(book_id)
            filename = title.split('::')[0].strip()
            download_url = f"https://tululu.org/txt.php?id={book_id}"
            filepath = download_txt(download_url, filename, book_id)  # передаем book_id
            print(f"Книга {book_id} скачана: {filepath}")
        except requests.exceptions.HTTPError as e:
            print(f"Ошибка скачивания книги {book_id}: {e}")


download_books()
