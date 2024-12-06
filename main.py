import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, unquote
import argparse


def check_for_redirect(response):
    if response.history and response.url == "https://tululu.org/":
        raise requests.exceptions.HTTPError("Redirected to the homepage")


def get_book_details(book_id):
    url = f"https://tululu.org/b{book_id}/"
    response = requests.get(url)

    try:
        check_for_redirect(response)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if 'Redirected to the homepage' in str(e):
            print(f"Ошибка скачивания книги {book_id}: редирект на главную")
            print()
        else:
            print(f"Ошибка скачивания книги {book_id}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    h1_text = soup.find('h1').get_text(strip=True)

    if '::' in h1_text:
        title, author = h1_text.split('::', 1)
        title = title.strip()
        author = author.strip()
    else:
        title = h1_text
        author = 'Неизвестен'

    cover_img_tag = soup.find('div', class_='bookimage').find('img')
    cover_url = cover_img_tag['src'] if cover_img_tag else None

    genre_tag = soup.find('span', class_='d_book')
    genre = None
    if genre_tag:
        genre_links = genre_tag.find_all('a')
        if genre_links:
            genre = genre_links[0].get_text(strip=True)

    book_data = {
        'title': title,
        'author': author,
        'genre': genre,
        'cover_url': cover_url
    }

    return book_data, soup


def create_folder(folder):
    os.makedirs(folder, exist_ok=True)


def download_file(url, folder, filename):
    response = requests.get(url)
    response.raise_for_status()
    create_folder(folder)
    filepath = os.path.join(folder, filename)
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def download_txt(url, filename, book_id, folder='books/'):
    if 'text/plain' not in requests.head(url).headers.get('Content-Type', ''):
        raise requests.exceptions.HTTPError("URL не ведет к текстовому файлу")
    return download_file(url, folder, f"{book_id}. {filename}.txt")


def download_image(url, folder='images/'):
    if 'image' not in requests.head(url).headers.get('Content-Type', ''):
        raise requests.exceptions.HTTPError("URL не ведет к изображению")
    path = urlsplit(url).path
    filename = os.path.basename(unquote(path))
    return download_file(url, folder, filename)


def save_comments(soup, book_id, folder='comments/'):
    comments = soup.find_all('div', class_='texts')
    create_folder(folder)
    filepath = os.path.join(folder, f"{book_id}. comments.txt")
    with open(filepath, 'w', encoding='utf-8') as file:
        for comment in comments:
            comment_text = comment.get_text(strip=True).split(')')[-1].strip()
            file.write(comment_text + '\n')


def download_books(start_id, end_id):
    for book_id in range(start_id, end_id + 1):
        try:
            result = get_book_details(book_id)
            if result is None:
                continue

            book_data, soup = result
            title = book_data['title']
            genre = book_data['genre']
            filename = title.split('::')[0].strip()

            print(f"{filename} - Жанр: {genre} - Автор: {book_data['author']}")
            print()

            download_url = f"https://tululu.org/txt.php?id={book_id}"
            download_txt(download_url, filename, book_id)

            if book_data['cover_url']:
                cover_url = f"https://tululu.org{book_data['cover_url']}"
                download_image(cover_url)

            save_comments(soup, book_id)

        except requests.exceptions.HTTPError as e:
            print(f"Ошибка скачивания книги {book_id}: {e}")
            print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Скачивание книг с сайта tululu.org")
    parser.add_argument('start_id', type=int, help="ID первой книги для скачивания")
    parser.add_argument('end_id', type=int, help="ID последней книги для скачивания")

    args = parser.parse_args()

    download_books(args.start_id, args.end_id)
