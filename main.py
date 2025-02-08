from dotenv import load_dotenv

load_dotenv()

import os
import requests

from datetime import datetime

def api_get(url, headers=None):
    # context = None
    if headers:
        context = {
            'http Headers': {'Authorization': f'Token {headers["client_id"]}:{headers["client_secret"]}'}
        }
    response = requests.get(base_url + url, allow_redirects=False, verify=True, stream=True)
    response.raise_for_status()
    return response.text

def api_get_json(url, headers=None):
    res = api_get(url, headers=headers)
    return eval(res)

def check_required_options(book_slug, out_folder):
    if not book_slug:
        print("Error: Book slug must be provided.")
        exit(1)
    if not out_folder or not os.path.isdir(out_folder) and not os.path.exists(out_folder):
        print("Error: Output folder must be a valid directory.")
        exit(1)

def create_output_directories(book_id, book_slug):
    out_dir = os.path.join(out_folder, book_slug)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    images_dir = os.path.join(out_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

def get_book_data(book_id):
    url = f"api/books/{book_id}"
    book_data = api_get_json(url)
    return book_data

def get_chapters_pages(chapter_url):
    chapters_content = api_get(f"{chapter_url}/list?limit=100")
    pages_content = api_get(f"{page_url}/list?limit=100")

    chapters_data = filter(lambda x: 'book_id' in x and x['book_id'] == book_id, json.loads(chapters_content))
    pages_data = filter(lambda x: 'book_id' in x and x['book_id'] == book_id, json.loads(pages_content))

    return list(chapters_data), list(pages_data)

def get_page_html(page):
    url = f"api/pages/{page['id']}"
    page_response = api_get_json(url)
    page_html = page_response.get('html', '')
    chapter = next((c for c in chapters if c['id'] == page['chapter_id']), None)

    return get_page_formatted_html(chapter, page_html), page

def extract_images(page_content):
    img_urls = [tag['url'] for tag in BeautifulSoup(page_content, "html.parser").find_all("img")]
    saved_images = {}
    for url in img_urls:
        if not os.path.exists(f"{images_dir}/{os.path.basename(url)}"):
            image_response = requests.get(url)
            with open(os.path.join(images_dir, os.path.basename(url)), 'wb') as f:
                f.write(image_response.content)
            saved_images[os.path.basename(url)] = 1
    for img in img_urls:
        if img not in saved_images and "local_secure" in img.lower():
            image_data = requests.get(img).content
            with open(os.path.join(images_dir, os.path.basename(img)), 'wb') as f:
                f.write(image_data)
            saved_images[img.split('/')[-1]] = 1

    return page_content

def write_files(chapters, direct_pages):
    book_index = '<html><head></head><body>'
    
    if chapters and pages:
        for chapter in chapters:
            out_file = os.path.join(out_dir, f"chapter{chapter['slug']}.html")
            with open(out_file, 'w') as file:
                book_index += f'<h3><a href="{out_file}">{chapter["name"]}</a></h3>'
                page_contents, pages_data = zip(*map(get_page_html, chapters))
                for content, p in zip(page_contents, pages_data):
                    page_html = extract_images(content.replace(url, "images/{os.path.basename(url)}"))
                    file.write(page_html)
    
    direct_page_contents = [get_page_html(page) for page in direct_pages]
    for page_content, page in direct_page_contents:
        out_file = os.path.join(out_dir, f"page{page['slug']}.html")
        with open(out_file, 'w') as file:
            book_index += f'<h3><a href="{out_file}">{page["name"]}</a></h3>'
            page_html = extract_images(page_content.replace(url, "images/{os.path.basename(url)}"))
            file.write(page_html)
    
    with open(os.path.join(out_dir, "index.html"), 'w') as index:
        index.write(book_index)

# Main script
base_url = "https://wiki.bytebolt.media/api"
client_id = os.getenv('BOOKSTACK_TOKEN_ID')
client_secret = os.getenv('BOOKSTACK_TOKEN_SECRET')


book_slug = input("Enter the book slug: ")
out_folder = input("Enter output folder path: ")

check_required_options(book_slug, out_folder)
chapters, pages = get_chapters_pages('/list')
book_data = get_book_data(chapters[0]['book_id'])
create_output_directories(book_data['id'], book_slug)
write_files(chapters, {p for p in pages if not any(ch['id'] == p['chapter_id'] for ch in chapters)})
