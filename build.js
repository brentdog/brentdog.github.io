const fs = require('fs');
const path = require('path');
const ejs = require('ejs');

const JSON_PATH = path.join(__dirname, 'albums.json');
const TEMPLATE_PATH = path.join(__dirname, 'template.ejs');
const DIST_DIR = path.join(__dirname, 'dist');
const OUTPUT_PATH = path.join(DIST_DIR, 'index.html');

function buildGallery() {
  try {
    const rawData = fs.readFileSync(JSON_PATH, 'utf8');
    const rawAlbums = JSON.parse(rawData);

    const albums = rawAlbums.map(album => ({
      title: album.title || 'Untitled Album',
      url: album.url || album.share_link || '#',
      thumbnail: album.thumbnail || album.thumbnail_link || ''
    }));

    // Format current timestamp (e.g., "October 9, 2026 at 4:55 PM UTC")
    const buildTime = new Date().toLocaleString('en-US', {
      dateStyle: 'long',
      timeStyle: 'short',
      timeZone: 'America/Denver'
    });

    if (!fs.existsSync(DIST_DIR)) {
      fs.mkdirSync(DIST_DIR, { recursive: true });
    }

    ejs.renderFile(TEMPLATE_PATH, { albums, buildTime }, (err, str) => {
      if (err) {
        console.error('Error rendering EJS template:', err);
        process.exit(1);
      }

      fs.writeFileSync(OUTPUT_PATH, str, 'utf8');
      console.log(`Successfully built gallery with ${albums.length} albums into dist/index.html`);
    });
  } catch (error) {
    console.error('Build process failed:', error);
    process.exit(1);
  }
}

buildGallery();
