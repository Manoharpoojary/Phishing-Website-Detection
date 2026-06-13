import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

def extract_web_features(url):
    features = {}

    try:
        response = requests.get(url, timeout=5)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
    except:
        # If site can't be reached → mark risky
        return {
            'IframeOrFrame': 0,
            'MissingTitle': 1,
            'PopUpWindow': 0,
            'RightClickDisabled': 0,
            'SubmitInfoToEmail': 0,
            'InsecureForms': 1,
            'ExtFormAction': 0,
            'AbnormalFormAction': 1,
            'ImagesOnlyInForm': 0,
            'PctExtHyperlinks': 0,
            'PctExtResourceUrls': 0,
            'ExtFavicon': 0
        }

    domain = urlparse(url).netloc

    # 1. Iframe detection
    features['IframeOrFrame'] = 1 if soup.find_all("iframe") else 0

    # 2. Missing title
    features['MissingTitle'] = 1 if not soup.title else 0

    # 3. Popup detection (basic)
    features['PopUpWindow'] = 1 if "window.open" in html else 0

    # 4. Right click disabled
    features['RightClickDisabled'] = 1 if "contextmenu" in html else 0

    # 5. Submit to email
    features['SubmitInfoToEmail'] = 1 if "mailto:" in html else 0

    # 6. Forms analysis
    forms = soup.find_all("form")

    insecure_forms = 0
    ext_forms = 0
    abnormal_forms = 0
    image_only_forms = 0

    for form in forms:
        action = form.get("action")

        if action:
            if not action.startswith("https"):
                insecure_forms += 1

            if domain not in action:
                ext_forms += 1
        else:
            abnormal_forms += 1

        # Check if form has only images
        inputs = form.find_all("input")
        imgs = form.find_all("img")
        if len(inputs) == 0 and len(imgs) > 0:
            image_only_forms += 1

    features['InsecureForms'] = 1 if insecure_forms > 0 else 0
    features['ExtFormAction'] = 1 if ext_forms > 0 else 0
    features['AbnormalFormAction'] = 1 if abnormal_forms > 0 else 0
    features['ImagesOnlyInForm'] = 1 if image_only_forms > 0 else 0

    # 7. External links
    links = soup.find_all("a", href=True)
    total_links = len(links)
    ext_links = 0

    for link in links:
        href = link['href']
        if domain not in href:
            ext_links += 1

    features['PctExtHyperlinks'] = ext_links / total_links if total_links > 0 else 0

    # 8. External resources (img, script, link)
    resources = soup.find_all(['img', 'script', 'link'])
    total_res = len(resources)
    ext_res = 0

    for tag in resources:
        src = tag.get('src') or tag.get('href')
        if src and domain not in src:
            ext_res += 1

    features['PctExtResourceUrls'] = ext_res / total_res if total_res > 0 else 0

    # 9. External favicon
    favicon = soup.find("link", rel="icon")
    if favicon and domain not in favicon.get("href", ""):
        features['ExtFavicon'] = 1
    else:
        features['ExtFavicon'] = 0

    return features

#example

url = "https://example.com"

features = extract_web_features(url)

for k, v in features.items():
    print(k, ":", v)