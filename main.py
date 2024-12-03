import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, unquote


# Функция для проверки редиректа
def check_for_redirect(response):
    if response.history and response.url == "https://tululu.org/":
        raise requests.exceptions.HTTPError("Redirected to the homepage")


# Получение данных о книге
def get_book_details(book_id):
    url = f"https://tululu.org/b{book_id}/"
    response = requests.get(url)
    check_for_redirect(response)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('h1').get_text()
    cover_img_tag = soup.find('div', class_='bookimage').find('img')  # Получаем тег с изображением
    cover_url = cover_img_tag['src'] if cover_img_tag else None
    return title, cover_url


# Скачивание текста книги
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


# Скачивание изображения (обложки)
def download_image(url, folder='images/'):
    response = requests.get(url)
    response.raise_for_status()
    if 'image' not in response.headers.get('Content-Type', ''):
        raise requests.exceptions.HTTPError("URL не ведет к изображению")

    # Получаем имя файла из URL
    path = urlsplit(url).path
    filename = os.path.basename(unquote(path))

    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    with open(filepath, 'wb') as file:
        file.write(response.content)

    return filepath


# Основная функция для скачивания книг и обложек
def download_books():
    for book_id in range(1, 11):
        try:
            title, cover_url = get_book_details(book_id)
            filename = title.split('::')[0].strip()
            download_url = f"https://tululu.org/txt.php?id={book_id}"
            txt_filepath = download_txt(download_url, filename, book_id)  # скачиваем текст книги
            print(f"Книга {book_id} скачана: {txt_filepath}")

            if cover_url:  # если есть обложка, скачиваем её
                cover_url = f"https://tululu.org{cover_url}"  # полный путь к изображению
                image_filepath = download_image(cover_url)
                print(f"Обложка для книги {book_id} скачана: {image_filepath}")
            else:
                print(f"Обложка для книги {book_id} не найдена.")

        except requests.exceptions.HTTPError as e:
            print(f"Ошибка скачивания книги {book_id}: {e}")


# Запуск скачивания
download_books()
