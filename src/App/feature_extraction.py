import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def is_valid_ip(ip_string):
    """Validate IP address with proper octet range (0-255)"""
    parts = ip_string.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False

def extract_domain_name(hostname):
    """Safely extract domain name from hostname"""
    if not hostname or '.' not in hostname:
        return ""
    parts = hostname.split('.')
    # Handle IP addresses
    if all(part.isdigit() for part in parts):
        return ""
    # Return second-to-last part (domain name before TLD)
    return parts[-2] if len(parts) >= 2 else ""

def extract_all_features(url, timeout=5):
    """
    Extract comprehensive features from URL for phishing detection

    Args:
        url: URL string to analyze
        timeout: Request timeout in seconds (default: 5)

    Returns:
        pandas DataFrame with extracted features
    """
    features = {}

    # Validate URL format
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Parse URL
    try:
        parsed = urlparse(url)
        hostname = parsed.netloc
        path = parsed.path
        query = parsed.query
        scheme = parsed.scheme
    except Exception as e:
        logger.warning(f"Failed to parse URL: {e}")
        raise ValueError(f"Invalid URL format: {url}")

    # -------- URL STRUCTURAL FEATURES --------
    features['NumDots'] = url.count('.')
    features['SubdomainLevel'] = hostname.count('.') - 1 if hostname else 0
    features['PathLevel'] = path.count('/')
    features['UrlLength'] = len(url)
    features['NumDash'] = url.count('-')

    # Hostname analysis
    features['NumDashInHostname'] = hostname.count('-')

    # Special characters
    features['AtSymbol'] = 1 if '@' in url else 0
    features['TildeSymbol'] = 1 if '~' in url else 0
    features['NumUnderscore'] = url.count('_')
    features['NumPercent'] = url.count('%')

    # Query parameters
    features['NumQueryComponents'] = len(query.split('&')) if query else 0
    features['NumAmpersand'] = url.count('&')
    features['NumHash'] = url.count('#')

    # Character composition
    features['NumNumericChars'] = sum(c.isdigit() for c in url)

    # Protocol security
    features['NoHttps'] = 0 if scheme == "https" else 1

    # -------- HOSTNAME FEATURES --------
    # Check for IP address (proper validation)
    features['IpAddress'] = 1 if is_valid_ip(hostname) else 0

    # Domain and subdomain analysis
    domain_name = extract_domain_name(hostname)
    hostname_without_port = hostname.split(':')[0]  # Remove port if present

    features['DomainInSubdomains'] = 1 if domain_name and domain_name in hostname_without_port.split('.')[0] else 0
    features['DomainInPaths'] = 1 if domain_name and domain_name in path.lower() else 0

    # Protocol in hostname (suspicious)
    features['HttpsInHostname'] = 1 if 'https' in hostname else 0

    features['HostnameLength'] = len(hostname_without_port)
    features['PathLength'] = len(path)
    features['QueryLength'] = len(query)

    # -------- PATH FEATURES --------
    features['DoubleSlashInPath'] = 1 if '//' in path else 0
    features['RandomString'] = 1 if re.search(r'[a-zA-Z]{10,}', path or hostname) else 0

    # -------- CONTENT ANALYSIS FEATURES --------
    features['NumSensitiveWords'] = len(re.findall(
        r'login|signin|verify|secure|account|confirm|update|auth|password|reset',
        url.lower()
    ))
    features['EmbeddedBrandName'] = 1 if re.search(
        r'paypal|google|facebook|amazon|apple|microsoft|bank|walmart|ebay',
        url.lower()
    ) else 0

    # -------- WEB PAGE FEATURES --------
    # SECURITY UPGRADE: Safe web scraping with SSL verification, content filtering, and size limits
    soup = None
    html = ""

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # SECURITY UPGRADE: Enable SSL verification and add content filtering
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            verify=True,  # Enable SSL certificate verification
            stream=True   # Stream content to limit memory usage
        )

        # Check content type for safety
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type and 'application/xhtml' not in content_type:
            logger.warning(f"Skipping non-HTML content for {url}: {content_type}")
            return features

        # Limit content size to prevent memory exhaustion (50KB max)
        content = response.raw.read(50000, decode_content=True)
        if len(content) >= 50000:
            logger.warning(f"Content too large for {url}, truncated to 50KB")

        soup = BeautifulSoup(content.decode('utf-8', errors='ignore'), "html.parser")
        html = content.decode('utf-8', errors='ignore')

    except requests.exceptions.SSLError as e:
        logger.warning(f"SSL certificate verification failed for {url}: {e}")
        soup = None
    except requests.Timeout:
        logger.warning(f"Request timeout for {url}")
        soup = None
    except requests.ConnectionError:
        logger.warning(f"Connection error for {url}")
        soup = None
    except requests.RequestException as e:
        logger.warning(f"Request failed for {url}: {e}")
        soup = None
    except Exception as e:
        logger.warning(f"Unexpected error fetching {url}: {e}")
        soup = None

    # Initialize defaults
    features.update({
        'PctExtHyperlinks': 0,
        'PctExtResourceUrls': 0,
        'ExtFavicon': 0,
        'InsecureForms': 0,
        'RelativeFormAction': 0,
        'ExtFormAction': 0,
        'AbnormalFormAction': 0,
        'PctNullSelfRedirectHyperlinks': 0,
        'FrequentDomainNameMismatch': 0,
        'FakeLinkInStatusBar': 0,
        'RightClickDisabled': 0,
        'PopUpWindow': 0,
        'SubmitInfoToEmail': 0,
        'IframeOrFrame': 0,
        'MissingTitle': 1,
        'ImagesOnlyInForm': 0
    })

    if soup:
        # -------- HYPERLINK ANALYSIS --------
        links = soup.find_all("a", href=True)
        total_links = len(links)
        ext_links = 0
        null_links = 0

        for link in links:
            href = link['href'].strip()
            # Handle protocol-relative URLs
            if href.startswith('//') or (href.startswith('http') and domain_name and domain_name not in href.lower()):
                ext_links += 1
            if href in ["#", "javascript:void(0)", "javascript:;", ""]:
                null_links += 1

        features['PctExtHyperlinks'] = ext_links / total_links if total_links > 0 else 0
        features['PctNullSelfRedirectHyperlinks'] = null_links / total_links if total_links > 0 else 0

        # -------- RESOURCE ANALYSIS --------
        resources = soup.find_all(['img', 'script', 'link'])
        total_res = len(resources)
        ext_res = 0

        for tag in resources:
            src = tag.get('src') or tag.get('href')
            if src:
                src = src.strip()
                if src.startswith('//') or (src.startswith('http') and domain_name and domain_name not in src.lower()):
                    ext_res += 1

        features['PctExtResourceUrls'] = ext_res / total_res if total_res > 0 else 0

        # -------- FAVICON ANALYSIS --------
        favicon = soup.find("link", rel=lambda x: x and "icon" in str(x).lower())
        if favicon:
            href = favicon.get("href", "").strip()
            if href and (href.startswith('//') or (href.startswith('http') and domain_name and domain_name not in href.lower())):
                features['ExtFavicon'] = 1

        # -------- FORM ANALYSIS --------
        forms = soup.find_all("form")
        for form in forms:
            action = form.get("action", "").strip()

            if action:
                if not action.startswith(("https", "/")):
                    features['InsecureForms'] = 1
                if action.startswith("//") or (action.startswith("http") and domain_name and domain_name not in action.lower()):
                    features['ExtFormAction'] = 1
                if action.startswith("/"):
                    features['RelativeFormAction'] = 1
            else:
                features['AbnormalFormAction'] = 1

            inputs = form.find_all("input")
            imgs = form.find_all("img")
            if len(inputs) == 0 and len(imgs) > 0:
                features['ImagesOnlyInForm'] = 1

        # -------- PAGE BEHAVIOR ANALYSIS --------
        features['IframeOrFrame'] = 1 if soup.find("iframe") or soup.find("frame") else 0
        features['MissingTitle'] = 1 if not soup.title or not soup.title.string else 0
        features['PopUpWindow'] = 1 if "window.open" in html else 0
        features['RightClickDisabled'] = 1 if "contextmenu" in html else 0
        features['SubmitInfoToEmail'] = 1 if "mailto:" in html else 0
        features['FakeLinkInStatusBar'] = 1 if "onmouseover" in html else 0

        # -------- DOMAIN MISMATCH ANALYSIS --------
        if total_links > 0:
            mismatch = sum(1 for link in links
                          if link['href'].startswith("http") and domain_name and domain_name not in link['href'].lower())
            features['FrequentDomainNameMismatch'] = 1 if mismatch > total_links * 0.5 else 0

    # -------- DERIVED FEATURES (Thresholds) --------
    features['SubdomainLevelRT'] = 1 if features['SubdomainLevel'] > 2 else 0
    features['UrlLengthRT'] = 1 if features['UrlLength'] > 75 else 0
    features['PctExtResourceUrlsRT'] = 1 if features['PctExtResourceUrls'] > 0.5 else 0
    features['AbnormalExtFormActionR'] = features['AbnormalFormAction']  # For model compatibility
    features['ExtMetaScriptLinkRT'] = 1 if features['PctExtResourceUrls'] > 0.5 else 0
    features['PctExtNullSelfRedirectHyperlinksRT'] = 1 if features['PctNullSelfRedirectHyperlinks'] > 0.5 else 0

    # -------- FEATURE ORDERING --------
    feature_order = [
        'NumDots', 'SubdomainLevel', 'PathLevel', 'UrlLength', 'NumDash', 'NumDashInHostname',
        'AtSymbol', 'TildeSymbol', 'NumUnderscore', 'NumPercent', 'NumQueryComponents',
        'NumAmpersand', 'NumHash', 'NumNumericChars', 'NoHttps', 'RandomString', 'IpAddress',
        'DomainInSubdomains', 'DomainInPaths', 'HttpsInHostname', 'HostnameLength', 'PathLength',
        'QueryLength', 'DoubleSlashInPath', 'NumSensitiveWords', 'EmbeddedBrandName',
        'PctExtHyperlinks', 'PctExtResourceUrls', 'ExtFavicon', 'InsecureForms',
        'RelativeFormAction', 'ExtFormAction', 'AbnormalFormAction',
        'PctNullSelfRedirectHyperlinks', 'FrequentDomainNameMismatch',
        'FakeLinkInStatusBar', 'RightClickDisabled', 'PopUpWindow', 'SubmitInfoToEmail',
        'IframeOrFrame', 'MissingTitle', 'ImagesOnlyInForm',
        'SubdomainLevelRT', 'UrlLengthRT', 'PctExtResourceUrlsRT',
        'AbnormalExtFormActionR', 'ExtMetaScriptLinkRT', 'PctExtNullSelfRedirectHyperlinksRT'
    ]

    # Return features in correct order as DataFrame
    ordered_features = {k: features[k] for k in feature_order}
    return pd.DataFrame([ordered_features])