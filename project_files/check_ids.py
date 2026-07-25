import re
with open('/Users/muhammedfurkankoruyan/Desktop/MyProject/KursBitirme/templates/cari_detay.html', 'r') as f:
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
