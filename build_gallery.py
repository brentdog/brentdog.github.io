import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

INPUT_FILE = "google_photos_albums.json"
CACHE_FILE = "cache.json"
OUTPUT_FILE = "index.html"

# Rate-limiting parameters
MAX_WORKERS = 5  # Keep low to avoid HTTP 429 rate limits
TIMEOUT = 10      # Timeout per HTTP request in seconds

def get_album_info(share_url, session, cache):
    # Return cached metadata if already fetched
    if share_url in cache:
        return cache[share_url]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    for attempt in range(3):
        try:
            res = session.get(share_url, headers=headers, allow_redirects=True, timeout=TIMEOUT)
            res.raise_for_status()

            # Extract title
            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', res.text)
            title = title_match.group(1) if title_match else "Photo Album"

            # Extract cover thumbnail
            image_match = re.search(r'<meta property="og:image" content="([^"]+)"', res.text)
            thumb = f"{image_match.group(1)}=w500-h500-c" if image_match else ""

            result = {"title": title, "link": share_url, "thumb": thumb}
            cache[share_url] = result
            return result
        except Exception as e:
            time.sleep(1.5 * (attempt + 1))  # Exponential backoff on retry

    print(f"[Warning] Failed to fetch metadata for: {share_url}")
    return {"title": "Photo Album", "link": share_url, "thumb": ""}

def generate_html(albums):
    grid_items = ""
    for album in albums:
        if not album.get("thumb"):
            continue
        grid_items += f'''
        <a href="{album['link']}" target="_blank" rel="noopener noreferrer" class="card">
            <img src="{album['thumb']}" alt="{album['title']}" loading="lazy" />
            <div class="card-title">{album['title']}</div>
        </a>
        '''

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Photo Galleries</title>
    <style>
        :root {{ --bg: #0f172a; --card-bg: #1e293b; --text: #f8fafc; }}
        body {{ font-family: system-ui, sans-serif; background-color: var(--bg); color: var(--text); padding: 2rem; margin: 0; }}
        h1 {{ text-align: center; margin-bottom: 2rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1.5rem; max-width: 1400px; margin: 0 auto; }}
        .card {{ background-color: var(--card-bg); border-radius: 12px; overflow: hidden; text-decoration: none; color: inherit; display: flex; flex-direction: column; transition: transform 0.2s, box-shadow 0.2s; }}
        .card:hover {{ transform: translateY(-4px); box-shadow: 0 10px 20px rgba(0,0,0,0.4); }}
        .card img {{ width: 100%; height: 240px; object-fit: cover; }}
        .card-title {{ padding: 1rem; font-weight: 600; text-align: center; font-size: 0.95rem; }}
    </style>
</head>
<body>
    <h1>Photo Galleries</h1>
    <div class="grid">{grid_items}</div>
</body>
</html>
'''
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found!")
        exit(1)

    with open(INPUT_FILE, "r") as f:
        urls = json.load(f)

    # Load cache if available
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    print(f"Processing {len(urls)} album links ({len(cache)} cached)...")

    results = []
    session = requests.Session()

    # Process links concurrently in small worker batches
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(get_album_info, url, session, cache): url for url in urls}
        for future in as_completed(future_to_url):
            results.append(future.result())

    # Save updated cache
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

    # Render gallery
    generate_html(results)
    print(f"Successfully processed {len(results)} albums and updated {OUTPUT_FILE}.")
