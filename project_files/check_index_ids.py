import re
with open('templates/index.html', 'r') as f:
    content = f.read()

ids_needed = [
    'musteriSayisi', 'tedarikciSayisi', 'toplamAlacak', 'toplamBorc',
    'toplamNakit', 'kasaBakiye', 'bankaBakiye',
    'toplamUrunCesidi', 'kritikStokSayisi', 'depoDolulukBar', 'depoDolulukOran',
    'odenmemisFatura', 'bekleyenIrsaliye', 'aylikFaturaTutari', 'taslakFatura'
]

html_ids = set(re.findall(r"id=['\"]([^'\"]+)['\"]", content))

missing = []
for jid in ids_needed:
    if jid not in html_ids:
        missing.append(jid)

print("Missing IDs:", missing)
