import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(BASE_DIR, 'templates', 'cari_detay.html')

with open(html_path, 'r') as f:
    content = f.read()

# Find all document.getElementById('...')
js_ids = re.findall(r"getElementById\('([^']+)'\)", content)
html_ids = re.findall(r"id=['\"]([^'\"]+)['\"]", content)

missing = []
for jid in js_ids:
    if jid not in html_ids:
        missing.append(jid)

if missing:
    print("Missing IDs:", set(missing))
else:
    print("All IDs used in JS exist in HTML.")
