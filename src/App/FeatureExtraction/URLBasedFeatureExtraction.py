import re
from urllib.parse import urlparse

def extract_url_features(url):
    features = {}

    parsed = urlparse(url)
    hostname = parsed.netloc
    path = parsed.path
    query = parsed.query

    # 1. Basic URL features
    features['NumDots'] = url.count('.')
    features['UrlLength'] = len(url)
    features['NumDash'] = url.count('-')
    features['NumUnderscore'] = url.count('_')
    features['NumPercent'] = url.count('%')
    features['NumAmpersand'] = url.count('&')
    features['NumHash'] = url.count('#')

    # 2. Special symbols
    features['AtSymbol'] = 1 if '@' in url else 0
    features['TildeSymbol'] = 1 if '~' in url else 0

    # 3. Numeric features
    features['NumNumericChars'] = sum(c.isdigit() for c in url)

    # 4. Domain-based
    features['SubdomainLevel'] = hostname.count('.') - 1 if hostname else 0
    features['HostnameLength'] = len(hostname)

    # 5. Path features
    features['PathLevel'] = path.count('/')
    features['PathLength'] = len(path)

    # 6. Query features
    features['QueryLength'] = len(query)
    features['NumQueryComponents'] = len(query.split('&')) if query else 0

    # 7. Security features
    features['NoHttps'] = 0 if url.startswith("https") else 1

    # 8. Suspicious patterns
    features['DoubleSlashInPath'] = 1 if '//' in path else 0
    features['HttpsInHostname'] = 1 if 'https' in hostname else 0

    # 9. IP address detection
    features['IpAddress'] = 1 if re.match(r'^\d{1,3}(\.\d{1,3}){3}', hostname) else 0

    return features

#example  

url = "http://secure-paypal-login123.xyz/login?id=45"

features = extract_url_features(url)

for k, v in features.items():
    print(k, ":", v)