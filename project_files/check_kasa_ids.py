import re
with open('templates/kasa_detay.html', 'r') as f:
    content = f.read()

js_ids = re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", content)
html_ids = set(re.findall(r"id=['\"]([^'\"]+)['\"]", content))

missing = []
for jid in set(js_ids):
    if jid not in html_ids:
        missing.append(jid)

print("Missing IDs:", missing)
