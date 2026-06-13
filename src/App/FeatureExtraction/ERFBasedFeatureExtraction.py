import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

def extract_external_features(url):
    features = {}

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
    except:
        return {
            'PctExtHyperlinks': 0,
            'PctExtResourceUrls': 0,
            'ExtFavicon': 0,
            'FrequentDomainNameMismatch': 1
        }

    domain = urlparse(url).netloc

    # 1️ Hyperlinks
    links = soup.find_all("a", href=True)
    total_links = len(links)
    ext_links = 0

    for link in links:
        href = link['href']
        if href.startswith("http") and domain not in href:
            ext_links += 1

    features['PctExtHyperlinks'] = ext_links / total_links if total_links > 0 else 0

    # 2️ Resource URLs (img, script, link)
    resources = soup.find_all(['img', 'script', 'link'])
    total_res = len(resources)
    ext_res = 0

    for tag in resources:
        src = tag.get('src') or tag.get('href')
        if src and src.startswith("http") and domain not in src:
            ext_res += 1

    features['PctExtResourceUrls'] = ext_res / total_res if total_res > 0 else 0

    # 3️ External favicon
    favicon = soup.find("link", rel=lambda x: x and "icon" in x.lower())
    if favicon:
        href = favicon.get("href", "")
        if href.startswith("http") and domain not in href:
            features['ExtFavicon'] = 1
        else:
            features['ExtFavicon'] = 0
    else:
        features['ExtFavicon'] = 0

    # 4️ Domain mismatch (simple logic)
    mismatch_count = 0

    for link in links:
        href = link['href']
        if href.startswith("http"):
            link_domain = urlparse(href).netloc
            if link_domain and link_domain != domain:
                mismatch_count += 1

    features['FrequentDomainNameMismatch'] = 1 if mismatch_count > (0.5 * total_links) else 0

    return features


#example

url = "https://example.com"

features = extract_external_features(url)

for k, v in features.items():
    print(k, ":", v)