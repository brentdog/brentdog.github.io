const fs = require('fs');
const path = require('path');

const JSON_PATH = path.join(__dirname, 'albums.json');

async function getThumbnailUrl(albumUrl) {
  try {
    const response = await fetch(albumUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36'
      },
      redirect: 'follow'
    });

    if (!response.ok) return '';

    const html = await response.text();

    const ogMatch = html.match(/<meta\s+property=["']og:image["']\s+content=["']([^"']+)["']/i) ||
                    html.match(/<meta\s+content=["']([^"']+)["']\s+property=["']og:image["']/i);
    if (ogMatch && ogMatch[1]) {
      return ogMatch[1];
    }

    const googleImgMatch = html.match(/(https:\/\/lh3\.googleusercontent\.com\/[^\s"'>]+)/i);
    if (googleImgMatch && googleImgMatch[1]) {
      return googleImgMatch[1];
    }

    return '';
  } catch (err) {
    console.error(`Failed to fetch cover for ${albumUrl}:`, err.message);
    return '';
  }
}

async function updateAlbumsJson() {
  const rawData = fs.readFileSync(JSON_PATH, 'utf8');
  const albums = JSON.parse(rawData);

  let updated = false;

  for (let i = 0; i < albums.length; i++) {
    const album = albums[i];
    if (!album.thumbnail) {
      console.log(`Fetching thumbnail for: ${album.title}`);
      const thumbnail = await getThumbnailUrl(album.url || album.share_link);
      if (thumbnail) {
        album.thumbnail = thumbnail;
        updated = true;
      }
      await new Promise(res => setTimeout(res, 300));
    }
  }

  if (updated) {
    fs.writeFileSync(JSON_PATH, JSON.stringify(albums, null, 2), 'utf8');
    console.log('Successfully updated missing thumbnails.');
  } else {
    console.log('No missing thumbnails found.');
  }
}

updateAlbumsJson();
