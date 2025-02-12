from dotenv import load_dotenv

load_dotenv()

import os
import json
import tqdm
import argparse
import requests

# API Credentials
API_URL = os.getenv('BS_URL', '')
CLIENT_ID = os.getenv('BS_TOKEN_ID', '')
CLIENT_SECRET = os.getenv('BS_TOKEN_SECRET', '')


# API Request functions
def api_get(endpoint):
    url = f"{API_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Token {CLIENT_ID}:{CLIENT_SECRET}"}
    response = requests.get(url, headers=headers)
    return response.text if response.ok else None


def api_get_json(endpoint):
    data = api_get(endpoint)
    return json.loads(data) if data else None


def get_book_by_slug(slug):
    endpoint = f'api/books?filter[slug]={slug}'
    resp = api_get_json(endpoint)
    book = resp['data'][0] if resp and 'data' in resp else None
    return api_get_json(f"api/books/{book['id']}") if book else None


def get_page_by_slug(slug):
    endpoint = f'api/pages?filter[slug]={slug}'
    resp = api_get_json(endpoint)
    page = resp['data'][0] if resp and 'data' in resp else None
    return api_get_json(f"api/pages/{page['id']}") if page else None


def get_all_page_ids_and_names():
    endpoint = 'api/pages'
    resp = api_get_json(endpoint)
    return [(page['id'], page['name']) for page in resp['data']] if resp and 'data' in resp else None


def get_all_book_ids_and_names():
    endpoint = 'api/books'
    resp = api_get_json(endpoint)
    return [(book['id'], book['name']) for book in resp['data']] if resp and 'data' in resp else None


def export_book(book_id: str, book_title: str = None):
    headers = {"Authorization": f"Token {CLIENT_ID}:{CLIENT_SECRET}"}
    endpoint = f"api/books/{book_id}/export/pdf"
    response = requests.get(f"{API_URL}/{endpoint}", headers=headers)
    # write the file
    if book_title:
        filename = book_title
    else:
        filename = get_book_by_slug(book_id)['slug']
    with open(f'{os.path.join(out_dir, f"{filename}.pdf")}', 'wb') as f:
        f.write(response.content)


def export_page(page_id: str, page_title: str = None):
    headers = {"Authorization": f"Token {CLIENT_ID}:{CLIENT_SECRET}"}
    endpoint = f"api/pages/{page_id}/export/pdf"
    response = requests.get(f"{API_URL}/{endpoint}", headers=headers)
    # write the file
    if page_title:
        filename = f"{page_title}.pdf"
    else:
        filename = f"{page_id}.pdf"
    with open(f'{os.path.join(out_dir, filename)}', 'wb') as f:
        f.write(response.content)


argparser = argparse.ArgumentParser(description="Export a book from BookStack to a static HTML site")
argparser.add_argument('--book_slug', help="The URL slug of the book to export", default=None)
argparser.add_argument('--page_slug', help="The URL slug of the page to export", default=None)
argparser.add_argument('--all-books', help="Export all books", action='store_true')
argparser.add_argument('--all-pages', help="Export all pages", action='store_true')
argparser.add_argument('--out', help="The folder to output the HTML files to", default="./output")
args = argparser.parse_args()

book_slug = args.book_slug
page_slug = args.page_slug
out_folder = args.out

# Ensure output directory exists
os.makedirs(out_folder, exist_ok=True)
out_dir = os.path.abspath(out_folder)

if book_slug and page_slug and not (args.all_books or args.all_pages):
    raise ValueError("You can only export a book or a page, not both")

if book_slug:
    book_data = get_book_by_slug(book_slug)
    book_id = book_data['id']
    export_book(book_id, book_slug)
elif page_slug:
    page_data = get_page_by_slug(page_slug)
    page_id = page_data['id']
    export_page(page_id, page_slug)
elif args.all_books:
    book_ids = get_all_book_ids_and_names()
    for book_id, book_name in tqdm.tqdm(book_ids, desc="Exporting books", unit="book"):
        export_book(book_id, book_name)
elif args.all_pages:
    page_ids = get_all_page_ids_and_names()
    for page_id, page_name in tqdm.tqdm(page_ids, desc="Exporting pages", unit="page"):
        export_page(page_id, page_name)
