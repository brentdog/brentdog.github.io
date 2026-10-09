import os
import json
import requests

CLIENT_ID = os.environ.get("GPHOTOS_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GPHOTOS_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("GPHOTOS_REFRESH_TOKEN")

def get_access_token():
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }
    res = requests.post(token_url, data=payload)
    res.raise_for_status()
    return res.json()["access_token"]

def fetch_albums(access_token):
    albums = []
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://photoslibrary.googleapis.com/v1/albums?pageSize=50"
    
    while url:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json()
        
        for item in data.get("albums", []):
            # Only include albums that have photos and a cover photo
            if "coverPhotoBaseUrl" in item:
                albums.append({
                    "title": item.get("title", "Untitled Album"),
                    "link": item.get("productUrl"),
                    # Append sizing parameters: width 500, height 500, cropped
                    "thumb": f"{item['coverPhotoBaseUrl']}=w500-h500-c"
                })
        
        page_token = data.get("nextPageToken")
        url = f"https://photoslibrary.googleapis.com/v1/albums?pageSize=50&pageToken={page_token}" if page_token else None

    return albums

def generate_html(albums):
    grid_items = ""
    for album in albums:
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
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text: #f8fafc;
        }}
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 2rem;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 1.5rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .card {{
            background-color: var(--card-bg);
            border-radius: 12px;
            overflow: hidden;
            text-decoration: none;
            color: inherit;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            display: flex;
            flex-direction: column;
        }}
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        }}
        .card img {{
            width: 100%;
            height: 240px;
            object-fit: cover;
        }}
        .card-title {{
            padding: 1rem;
            font-weight: 600;
            font-size: 1rem;
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>Photo Galleries</h1>
    <div class="grid">
        {grid_items}
    </div>
</body>
</html>
'''
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    token = get_access_token()
    albums = fetch_albums(token)
    generate_html(albums)
    print(f"Successfully generated gallery with {len(albums)} albums.")
