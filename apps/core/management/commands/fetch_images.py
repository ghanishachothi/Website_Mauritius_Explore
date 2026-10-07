"""One-off helper: download free Commons images for each experience folder."""
import json
import os
import urllib.parse
import urllib.request

UA = {'User-Agent': 'MauritiusExplore-seed/1.0 (student project; contact: suwaibahradim@gmail.com)'}
STATIC_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'static'))

WANTED = {
    'ile-aux-cerfs-catamaran-day': ['catamaran mauritius', 'ile aux cerfs beach'],
    'blue-bay-snorkelling-adventure': ['blue bay mauritius snorkelling', 'coral reef fish underwater mauritius'],
    'chamarel-waterfall': ['chamarel falls mauritius', 'chamarel waterfall'],
    'sunset-kayak-at-mont-choisy': ['mont choisy beach sunset', 'mont choisy beach'],
    'le-morne-summit-hike': ['le morne brabant trail', 'le morne brabant mauritius'],
    'chamarel-food-tour': ['mauritian street food', 'mauritius rum distillery'],
    'grand-baie-street-festival': ['grand baie mauritius', 'sega dance mauritius'],
    '_hero': ['mauritius coast aerial', 'mauritius beach lagoon'],
}


def api_search(term, limit=8):
    params = urllib.parse.urlencode({
        'action': 'query', 'format': 'json', 'generator': 'search',
        'gsrsearch': f'filetype:bitmap {term}', 'gsrlimit': limit,
        'gsrnamespace': 6, 'prop': 'imageinfo',
        'iiprop': 'url|size|mime', 'iiurlwidth': 900,
    })
    url = f'https://commons.wikimedia.org/w/api.php?{params}'
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def pick(data):
    pages = data.get('query', {}).get('pages', {})
    best = None
    for page in pages.values():
        infos = page.get('imageinfo') or []
        if not infos:
            continue
        info = infos[0]
        if info.get('mime') not in ('image/jpeg', 'image/png'):
            continue
        w, h = info.get('width', 0), info.get('height', 0)
        if w < 800 or h < 500 or h > w * 1.5:
            continue
        score = w + h
        if best is None or score > best[0]:
            best = (score, info.get('thumburl') or info.get('url'))
    return best[1] if best else None


def download(url, path):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp, open(path, 'wb') as fh:
        fh.write(resp.read())


def main():
    for folder, terms in WANTED.items():
        safe = folder.lstrip('_')
        out_dir = os.path.join(STATIC_ROOT, 'images', 'explore_your_way' if folder == '_hero' else 'events', safe)
        os.makedirs(out_dir, exist_ok=True)
        count = 0
        for term in terms:
            try:
                data = api_search(term)
            except Exception as exc:  # noqa: BLE001
                print(f'  search failed for "{term}": {exc}')
                continue
            pages = data.get('query', {}).get('pages', {})
            candidates = []
            for page in pages.values():
                infos = page.get('imageinfo') or []
                if not infos:
                    continue
                info = infos[0]
                if info.get('mime') not in ('image/jpeg', 'image/png'):
                    continue
                w, h = info.get('width', 0), info.get('height', 0)
                if w < 800 or h < 500 or h > w * 1.5:
                    continue
                candidates.append((w + h, info.get('thumburl') or info.get('url')))
            candidates.sort(reverse=True)
            for _, url in candidates:
                if count >= 3:
                    break
                name = f'{safe}-{count + 1}.jpg'
                try:
                    download(url, os.path.join(out_dir, name))
                    print(f'  saved {folder}/{name}')
                    count += 1
                except Exception as exc:  # noqa: BLE001
                    print(f'  download failed: {exc}')


if __name__ == '__main__':
    main()
