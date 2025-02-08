from dotenv import load_dotenv

load_dotenv()

import os
import sys
import json
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


def export_book(book_id: str):
    headers = {"Authorization": f"Token {CLIENT_ID}:{CLIENT_SECRET}"}
    endpoint = f"api/books/{book_id}/export/pdf"
    response = requests.get(f"{API_URL}/{endpoint}", headers=headers)
    # write the file
    with open(f'{os.path.join(out_dir, f"{book_slug}.pdf")}', 'wb') as f:
        f.write(response.content)


argparser = argparse.ArgumentParser(description="Export a book from BookStack to a static HTML site")
argparser.add_argument('book_slug', help="The URL slug of the book to export")
argparser.add_argument('output_folder', help="The folder to output the HTML files to")
args = argparser.parse_args()


book_slug = args.book_slug
out_folder = args.output_folder

# Ensure output directory exists
os.makedirs(out_folder, exist_ok=True)
out_dir = os.path.abspath(out_folder)

book_data = get_book_by_slug(book_slug)
book_id = book_data['id']
export_book(book_id)
