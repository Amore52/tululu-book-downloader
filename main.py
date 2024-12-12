import os
import requests
from bs4 import BeautifulSoup
import argparse
from urllib.parse import urlsplit, unquote, urlencode, urlunparse
import time
from requests.exceptions import RequestException, ConnectionError


def check_for_redirect(response):
    if response.history and response.url == "https://tululu.org/":
        raise requests.exceptions.HTTPError("Redirected to the homepage")


def fetch_page(url, retries=3, delay=5):
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url)
            check_for_redirect(response)
            response.raise_for_status()
            return response.text
        except (RequestException, ConnectionError) as e:
            attempt += 1
            print(f"Попытка {attempt} не удалась: {e}")
            if attempt < retries:
                print(f"Попробуем снова через {delay} секунд...")
                time.sleep(delay)
            else:
                print(f"Не удалось загрузить страницу {url} после {retries} попыток.")
                return None


def parse_book_page(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    h1_text = soup.find('h1').get_text(strip=True)
    title, author = (h1_text.split('::', 1) + ['Неизвестен'])[:2]
    title = title.strip()
    author = author.strip()
    cover_img_tag = soup.find('div', class_='bookimage').find('img')
    cover_url = cover_img_tag['src'] if cover_img_tag else None
    genre_tag = soup.find('span', class_='d_book')
    genre = genre_tag.find('a').get_text(strip=True) if genre_tag else None
    comments = [
        comment.get_text(strip=True).split(')')[-1].strip()
        for comment in soup.find_all('div', class_='texts')
    ]
    return {'title': title, 'author': author, 'genre': genre, 'cover_url': cover_url, 'comments': comments}


def download_file(url, folder, filename, retries=3, delay=5):
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url)
            response.raise_for_status()
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, filename), 'wb') as file:
                file.write(response.content)
            return
        except (RequestException, ConnectionError) as e:
            attempt += 1
            print(f"Попытка {attempt} не удалась: {e}")
            if attempt < retries:
                print(f"Попробуем снова через {delay} секунд...")
                time.sleep(delay)
            else:
                print(f"Не удалось скачать файл {url} после {retries} попыток.")


def save_comments(comments, book_id, folder='comments/'):
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{book_id}. comments.txt")
    with open(filepath, 'w', encoding='utf-8') as file:
        file.writelines([f"{comment}\n" for comment in comments])


def download_book(book_id):
    url = f"https://tululu.org/b{book_id}/"
    page_content = fetch_page(url)
    if not page_content:
        return

    book_info = parse_book_page(page_content)
    title, genre, author = book_info['title'], book_info['genre'], book_info['author']
    filename = title.split('::')[0].strip()
    print(f"{filename} - Жанр: {genre} - Автор: {author}\n")
    params = {'id': book_id}
    download_url = urlunparse(('https', 'tululu.org', '/txt.php', '', urlencode(params), ''))
    download_file(download_url, 'books', f"{book_id}. {filename}.txt")
    if book_info['cover_url']:
        cover_url = f"https://tululu.org{book_info['cover_url']}"
        download_file(cover_url, 'images', os.path.basename(unquote(urlsplit(cover_url).path)))
    save_comments(book_info['comments'], book_id)


def download_books(start_id, end_id):
    for book_id in range(start_id, end_id + 1):
        yield book_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Скачивание книг с сайта tululu.org")
    parser.add_argument('start_id', type=int, help="ID первой книги для скачивания")
    parser.add_argument('end_id', type=int, help="ID последней книги для скачивания")

    args = parser.parse_args()

    # Генератор книг и обработка каждой
    for book_id in download_books(args.start_id, args.end_id):
        download_book(book_id)
